# src/api/auth/router.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session

from src.core.deps import get_users_db
from src.core.security import parse_token, blacklist_token
from src.core.config import ACCESS, REFRESHED
from src.schemas.security import LogOutResponse

from src.api.auth.schemas import SignUpRequest, SignUpResponse, LogInRequest, LogInResponse
from src.api.auth.service import create_user, authenticate_user, create_access_token

router = APIRouter()

@router.post("/sign-up", status_code= status.HTTP_201_CREATED,
             summary= "회원가입", description= "신규 사용자 회원가입 API. 이름, ID, PW 를 입력받음",)
def sign_up(signup_in: SignUpRequest, db: Session = Depends(get_users_db)) -> SignUpResponse:
    user = create_user(db, signup_in.user_id, signup_in.user_name, signup_in.password)
    if not user:
        raise HTTPException(status_code= status.HTTP_409_CONFLICT, detail= "이미 사용중인 ID 입니다.")
    return SignUpResponse(status= "success", 
                          user_name= user.user_name, 
                          user_id= user.user_id)

@router.post("/log-in", status_code= status.HTTP_200_OK, 
             summary= "로그인", description= "사용자의 ID, PW 를 입력받음")
def login(login_in: LogInRequest, response: Response, db: Session = Depends(get_users_db)) -> LogInResponse:
    user = authenticate_user(db, login_in.user_id, login_in.password)
    if not user:
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= "아이디/비밀번호 불일치")
    token = create_access_token(data= {"user_id": user.user_id})
    response.set_cookie(
        key= ACCESS,
        value= token,
        httponly= True,     # JS로 접근 불가, XSS 보호
        secure= True,       # HTTPS에서만 전송
        samesite= "lax",    # 필요시 "strict" 등 조정
        max_age= 3600,      # 쿠키 만료 (초)
        path= "/"
    )
    return LogInResponse( status= "success",
                          user_name= user.user_name,
                          user_id= user.user_id)

@router.post("/log-out", status_code= status.HTTP_200_OK,
             summary= "로그아웃", description= "JWT/Refresh 토큰 블랙리스트 등록 및 쿠키 삭제")
def logout(request: Request, response: Response) -> LogOutResponse:
    # 쿠키에서 토큰 추출
    token = request.cookies.get(ACCESS)
    refresh_token = request.cookies.get(REFRESHED)
    if not token and not refresh_token:
        raise HTTPException(status_code= 401, detail= "로그인 상태가 아닙니다.")
    # 토큰에서 jti 추출 후 JTI-블랙리스트 등록
    if token:
        jti, exp = parse_token(token)
        blacklist_token(jti, exp) # DB에 등록
    if refresh_token:
        jti_r, exp_r = parse_token(refresh_token)
        blacklist_token(jti_r, exp_r) # Refresh 토큰도 블랙리스트 처리
    # 쿠키 삭제 (프론트에도 적용해야 함)
    response.delete_cookie(ACCESS)
    response.delete_cookie(REFRESHED)
    return LogOutResponse(status= "success", message= "로그아웃 되었습니다.")