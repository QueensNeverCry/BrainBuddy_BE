# src/api/auth/router.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from sqlalchemy.orm import Session

from src.core.deps import get_users_db, get_user
from src.core.security import get_payload, parse_token, blacklist_token, is_token_blacklisted
from src.core.config import ACCESS, REFRESH, ACCESS_TOKEN_EXPIRE_SEC, REFRESH_TOKEN_EXPIRE_SEC
from src.schemas.security import LogOutResponse
from src.models.users import User

from src.api.auth.schemas import SignUpRequest, SignUpResponse, LogInRequest, LogInResponse, TokenResponse
from src.api.auth.service import create_user, authenticate_user, create_access_token, create_refresh_token

router = APIRouter()

@router.post("/auth/sign-up", 
             status_code= status.HTTP_201_CREATED,
             summary= "회원가입", 
             description= "신규 사용자 회원가입 API. 이름, ID, PW 를 입력받음")
def sign_up(signup_in: SignUpRequest, db: Session = Depends(get_users_db)) -> SignUpResponse:
    user = create_user(db, signup_in.user_id, signup_in.user_name, signup_in.password)
    if not user:
        raise HTTPException(status_code= status.HTTP_409_CONFLICT, detail= "이미 사용중인 ID 입니다.")
    return SignUpResponse(status= "success", 
                          user_name= user.user_name, 
                          user_id= user.user_id)

@router.post("/auth/log-in", 
             status_code= status.HTTP_200_OK, 
             summary= "로그인", 
             description= "사용자의 ID, PW 를 입력받음")
def login(login_in: LogInRequest, response: Response, db: Session = Depends(get_users_db)) -> LogInResponse:
    user = authenticate_user(db, login_in.user_id, login_in.password)
    if not user:
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= "아이디/비밀번호 불일치")
    access_token = create_access_token(data= {"user_id": user.user_id})
    refresh_token = create_refresh_token(data={"user_id": user.user_id})
    # response - cookie에 JWT ACCESS TOKEN 설정
    response.set_cookie( key= ACCESS,
                         value= access_token,
                         httponly= True,     # JS로 접근 불가, XSS 보호
                         secure= True,       # HTTPS에서만 전송
                         samesite= "lax",    # 필요시 "strict" 등 조정
                         max_age= ACCESS_TOKEN_EXPIRE_SEC,
                         path= "/")
    # response - cookie에 JWT REFRESH TOKEN 설정
    response.set_cookie( key= REFRESH,
                         value= refresh_token,
                         httponly= True,
                         secure= True,
                         samesite= "lax",
                         max_age= REFRESH_TOKEN_EXPIRE_SEC,
                         path= "/")
    return LogInResponse( status= "success",
                          user_name= user.user_name,
                          user_id= user.user_id)

@router.post("/auth/refresh", 
             status_code= status.HTTP_200_OK,
             summary= "JWT ACCESS 토큰 재발급", 
             description= "Refresh 토큰의 유효성 검사 후 새로운 Access 토큰을 반환")
def renew_access_token(request: Request, response: Response, db: Session = Depends(get_users_db)) -> TokenResponse:
    refresh_token = request.cookies.get(REFRESH)
    if not refresh_token:
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= "There is no Refresh Token in cookie. Login plz")
    try:
        payload = get_payload(refresh_token) # JWT 검증 및 payload 추출
        if is_token_blacklisted(payload["jti"]):
            raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail="블랙리스트 등록된 토큰입니다. 재로그인 필요")
        user_id = payload.get("user_id")
        if not user_id:
            raise ValueError("No user_id in Refresh token.")
        user = db.query(User).filter(User.user_id == user_id).first()
        # 존재하지 않는 사용자
        if user is None:
            raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail="존재하지 않는 사용자")
        # 영구정지/차단된 사용자
        if user.status == "banned":   # 또는 user.is_active == False 등
            raise HTTPException(status_code= status.HTTP_403_FORBIDDEN, detail="정지된 사용자")
    except Exception as e:
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= "Refresh Token is not valid. Login plz.")
    # 새로운 ACCESS 토큰 생성
    new_access_token = create_access_token({"user_id": user_id})
    # 새로운 ACCESS 토큰을 쿠키에 httpOnly, secure로 발급
    response.set_cookie( key= ACCESS,
                         value= new_access_token,
                         httponly= True,
                         secure= True,
                         samesite= "lax",
                         max_age= ACCESS_TOKEN_EXPIRE_SEC,
                         path= "/" )
    return TokenResponse(status= "success")
        

@router.post("/auth/log-out", 
             status_code= status.HTTP_200_OK,
             summary= "로그아웃", 
             description= "JWT/Refresh 토큰 블랙리스트 등록 및 쿠키 삭제")
def logout(request: Request, response: Response) -> LogOutResponse:
    # 쿠키에서 토큰 추출
    token = request.cookies.get(ACCESS)
    refresh_token = request.cookies.get(REFRESH)
    if not token and not refresh_token:
        raise HTTPException(status_code= 401, detail= "로그인 상태가 아닙니다.")
    # 토큰에서 jti 추출 후 JTI-블랙리스트 등록
    if token:
        jti, exp = parse_token(token)
        blacklist_token(jti, exp) # ACCESS token 블랙리스트에 등록
    if refresh_token:
        jti_r, exp_r = parse_token(refresh_token)
        blacklist_token(jti_r, exp_r) # REFRESH token 도 블랙리스트 처리
    # 쿠키 삭제 (프론트는 안해도 됨)
    response.delete_cookie(ACCESS)
    response.delete_cookie(REFRESH)
    return LogOutResponse(status= "success", message= "로그아웃 되었습니다.")