# src/api/auth/router.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from src.core.deps import get_users_db
from src.core.security import get_payload, parse_token, blacklist_token
from src.core.config import ACCESS, REFRESH, ACCESS_TOKEN_EXPIRE_SEC, REFRESH_TOKEN_EXPIRE_SEC
from src.schemas.security import LogOutResponse
from src.models.users import User

from src.api.auth.schemas import SignUpRequest, SignUpResponse, LogInRequest, LogInResponse, RenewResponse, WithdrawRequest, WithdrawResponse
from src.api.auth.service import add_user, get_user_by_id, erase_user_by_id, authenticate_user, create_access_token, create_refresh_token, add_refresh_token, check_refresh_token, erase_refresh_token



router = APIRouter()


# 회원 가입 API [POST  https://{Server DNS}/api/auth/sign-up]
@router.post("/auth/sign-up", 
             status_code= status.HTTP_201_CREATED,
             summary= "회원가입", 
             description= "신규 사용자 회원가입 API. 이름, ID, PW 를 입력받음")
def sign_up(signup_in: SignUpRequest, db: Session = Depends(get_users_db)) -> SignUpResponse:
    user = add_user(db, signup_in.user_id, signup_in.user_name, signup_in.password)
    if not user:
        raise HTTPException(status_code= status.HTTP_409_CONFLICT, detail= "이미 사용중인 ID 입니다.")
    return SignUpResponse(status= "success", 
                          user_name= user.user_name, 
                          user_id= user.user_id)


# 로그인 API [POST  https://{Server DNS}/api/auth/log-in]
@router.post("/auth/log-in", 
             status_code= status.HTTP_200_OK, 
             summary= "로그인", 
             description= "사용자의 ID, PW 를 입력받음")
def login(login_in: LogInRequest, response: Response, db: Session = Depends(get_users_db)) -> LogInResponse:
    user = authenticate_user(db, login_in.user_id, login_in.password)
    if not user:
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= "아이디/비밀번호 불일치")
    access_token = create_access_token(data= {"user_id": user.user_id})
    refresh_token = create_refresh_token(db, data={"user_id": user.user_id})
    # 현재 Users, RefreshTokens 테이블은 동일DB
    add_refresh_token(db, refresh_token, user.user_id, login_in.device_id)
    # response - cookie에 JWT ACCESS TOKEN 설정
    response.set_cookie( key= ACCESS,
                         value= access_token,
                         httponly= True,     # JS로 접근 불가, XSS 공격 방지
                         secure= True,       # HTTPS에서만 전송
                         samesite= "strict", # CSRF 공격 방지, BrainBuddy 도메인에서 출발한 요청에만 브라우저가 쿠키 첨부 !
                         max_age= ACCESS_TOKEN_EXPIRE_SEC,
                         path= "/")
    # response - cookie에 JWT REFRESH TOKEN 설정
    response.set_cookie( key= REFRESH,
                         value= refresh_token,
                         httponly= True,
                         secure= True,
                         samesite= "strict",
                         max_age= REFRESH_TOKEN_EXPIRE_SEC,
                         path= "/")
    return LogInResponse( status= "success",
                          user_name= user.user_name,
                          user_id= user.user_id)


# Access Token Refresh 요청 API [POST  https://{Server DNS}/api/auth/refresh]
@router.post("/auth/refresh", 
             status_code= status.HTTP_200_OK,
             summary= "JWT ACCESS 토큰 재발급", 
             description= "Refresh 토큰의 유효성 검사 후 새로운 Access / Refresh 토큰을 반환")
def renew_access_token(request: Request, response: Response, db: Session = Depends(get_users_db)) -> RenewResponse:
    refresh_token = request.cookies.get(REFRESH)
    erase_refresh_token(db, refresh_token)
    if not refresh_token:
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= "There is no Refresh Token in cookie. Login plz")
    try:
        refresh_payload = check_refresh_token(refresh_token) # JWT 검증 및 payload 추출
        user_id = refresh_payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR, detail="토큰 decoding 실패")
        user = db.query(User).filter(User.user_id == user_id).first()
        # 존재하지 않는 사용자
        if user is None:
            raise HTTPException(status_code= status.HTTP_404_UNAUTHORIZED, detail="없는데요 ?")
        # 영구정지/차단된 사용자
        if user.status == "banned":   # 또는 user.is_active == False 등
            raise HTTPException(status_code= status.HTTP_403_FORBIDDEN, detail="정지된 사용자")
    except Exception as e:
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= "Refresh Token is not valid. Login plz.")
    # 새로운 ACCESS 토큰 생성
    new_access_token = create_access_token({"user_id": user_id})
    new_refresh_token = create_refresh_token(data={"user_id": user_id})
    add_refresh_token(db, new_refresh_token, user.user_id)
    # 새로운 ACCESS, REFRESH 토큰을 쿠키에 httpOnly, secure로 발급
    response.set_cookie( key= ACCESS,
                         value= new_access_token,
                         httponly= True,
                         secure= True,
                         samesite= "strict",
                         max_age= ACCESS_TOKEN_EXPIRE_SEC,
                         path= "/" )
    response.set_cookie( key= REFRESH,
                         value= new_refresh_token,
                         httponly= True,
                         secure= True,
                         samesite= "strict",
                         max_age= REFRESH_TOKEN_EXPIRE_SEC,
                         path= "/")
    return RenewResponse(status= "success")
        

# 로그아웃 API [POST  https://{Server DNS}/api/auth/log-out]
@router.post("/auth/log-out", 
             status_code= status.HTTP_200_OK,
             summary= "로그아웃", 
             description= "JWT/Refresh 토큰 블랙리스트 등록 및 쿠키 삭제")
def logout(request: Request, response: Response, db: Session = Depends(get_users_db)) -> LogOutResponse:
    # 쿠키에서 토큰 추출
    token = request.cookies.get(ACCESS)
    refresh_token = request.cookies.get(REFRESH)
    if not token or not refresh_token:
        raise HTTPException(status_code= status.HTTP_403_FORBIDDEN, detail= "로그인 상태가 아닙니다.")
    # 토큰에서 jti 추출 후 JTI-블랙리스트 등록
    if token:
        jti, exp = parse_token(token)
        if datetime.now() > exp :
            raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= "이미 로그아웃 된 상태")
        else:
            blacklist_token(jti, exp) # ACCESS token 블랙리스트에 등록
    if refresh_token:
        jti_r, exp_r = parse_token(refresh_token)
        blacklist_token(jti_r, exp_r) # REFRESH token 도 블랙리스트 처리
        # 사용자의 refresh_token DB 에서 삭제, 만료 또는 변조되었더라도 UX 고려 로그아웃 처리
        erase_refresh_token(db, refresh_token)
    # 쿠키 삭제
    response.delete_cookie(key= ACCESS, path="/")
    response.delete_cookie(key= REFRESH, path="/")
    return LogOutResponse(status= "success", message= "로그아웃 되었습니다.")


# 회원탈퇴 API [DELETE  https://{Server DNS}/api/auth/delete-account]
@router.delete("/auth/delete-account",
               status_code= status.HTTP_200_OK,
               summary= "회원탈퇴",
               description= "가입한 사용자의 회원 탈퇴")
def delete_user(request: Request, response: Response, db: Session = Depends(get_users_db)) -> WithdrawResponse:
    token = request.cookies.get(ACCESS)
    refresh_token = request.cookies.get(REFRESH)
    user_id = request.body["user_id"]
    if not token or not refresh_token:
        raise HTTPException(status_code= status.HTTP_403_FORBIDDEN, detail= "토큰이 존재하지 않습니다.")
    try:
        payload = get_payload(token)
        user_id = payload.get("user_id")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰이 유효하지 않습니다.")
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 사용자입니다.")
    else:
        try:
            erase_user_by_id(db, user_id)
        except Exception:
            raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR, detail="회원 탈퇴 처리 중 서버 오류가 발생했습니다.")
    try:
        jti, exp = parse_token(token)
        blacklist_token(jti, exp)
    except Exception:
        pass
    try:
        jti_r, exp_r = parse_token(refresh_token)
        blacklist_token(jti_r, exp_r)
        erase_refresh_token(db, refresh_token)
    except Exception:
        pass
    # 쿠키 삭제
    response.delete_cookie(key= ACCESS, path= "/")
    response.delete_cookie(key= REFRESH, path="/")
    return WithdrawResponse(status="success", message="회원 탈퇴가 정상 처리되었습니다.")