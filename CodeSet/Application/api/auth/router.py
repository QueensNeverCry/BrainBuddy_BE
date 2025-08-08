from fastapi import APIRouter, Request, Response, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from Application.core.deps import AsyncDB, GetCurrentUser
from Application.core.config import ACCESS, REFRESH
from Application.core.security import Token
from Application.core.exceptions import Server, TokenAuth

from Application.api.auth.schemas import SignUpRequest, SignUpResponse, LogInRequest, LogInResponse, RenewResponse, LogOutResponse, WithdrawRequest, WithdrawResponse
from Application.api.auth.service import AuthService
from Application.api.auth.exceptions import SignUp, Login, Withdraw



router = APIRouter()



# --- 회원가입 API [HTTPS POST : https://{ServerDNS}/api/auth/sign-up] ---
@router.post("/sign-up",
             status_code=status.HTTP_201_CREATED,
             summary="Sign Up",
             description="신규 사용자 회원가입 API. 이름, ID, PW 를 입력받음")
# 필드의 존재 여부, 형식 검사, pw 와 pw_confirm 확인은 pydantic model 단에서 완료 -> user_id 의 중복 확인만 수행
async def sign_up(request: SignUpRequest,
                  db: AsyncSession = Depends(AsyncDB.get_db)) -> SignUpResponse:
    try:
        await db.begin()
        email = request.email
        user_name = request.user_name
        print(f"[LOG] : {user_name} requested sign - up.")
        if await AuthService.check_duplicate(db, email, user_name):
            raise SignUp.USER_EXISTS.exc()
        # 비밀번호 해싱 및 DB 저장
        await AuthService.register_user(db, request)
        # commit & api response
        await db.commit()
        return SignUpResponse(user_name=user_name)
    except SQLAlchemyError:
        await db.rollback()
        raise Server.DB_ERROR.exc()



# --- 로그인 API [HTTP POST : https://{ServerDNS}/api/auth/log-in] ---
@router.post("/log-in", 
             status_code= status.HTTP_200_OK,
             summary= "Log-in", 
             description= "사용자의 ID, PW 를 입력받음")
async def login(request: LogInRequest,
                response: Response,
                db: AsyncSession = Depends(AsyncDB.get_db)) -> LogInResponse:
    try:
        await db.begin()
        # ID 와 PW 가 일치한 사용자 조회
        user = await AuthService.find_user(db, request=request)
        if not user:
            raise Login.USER_NOT_FOUND.exc()
        access_token = Token.create_access_token(user.user_name)
        refresh_token = Token.create_refresh_token(user.user_name)
        # print(f"{user.user_name}")
        await AuthService.add_refresh_token(db, refresh_token, user.user_name)
        # response - cookie에 JWT ACCESS TOKEN 설정
        AuthService.set_cookies(response, access_token, refresh_token)
        await db.commit()
        return LogInResponse(user_name= user.user_name)
    except SQLAlchemyError:
        await db.rollback()
        raise Server.DB_ERROR.exc()



# --- Token 재발급 요청 API [HTTP POST : https://{ServerDNS}/api/auth/refresh] ---
@router.post("/refresh", 
             status_code= status.HTTP_200_OK,
             summary= "Refresh Tokens", 
             description= "사용자의 Access / Refresh Tokens 를 쿠키를 통해 입력받음")
async def renew_tokens(request: Request,
                       response: Response, 
                       db: AsyncSession = Depends(AsyncDB.get_db),
                       name: str = Depends(GetCurrentUser)) -> RenewResponse:
    old_access = request.cookies.get(ACCESS)
    old_refresh = request.cookies.get(REFRESH)
    try:
        await db.begin()
        # 두 token 모두 존재, 모든 claim 검증, user_email 일치 확인
        if not await Token.is_normal_tokens(db, old_access, old_refresh, name):
            AuthService.clear_cookies(response)
            raise TokenAuth.TOKEN_INVALID.exc()
        # Refresh 토큰의 revoked 여부 확인
        if await Token.is_refresh_revoked(db, old_access, old_refresh):
            AuthService.clear_cookies(response)
            raise TokenAuth.TOKEN_INVALID.exc()
        # Refresh 토큰의 만료 여부 확인
        if Token.is_refresh_expired(old_refresh):
            AuthService.clear_cookies(response)
            raise TokenAuth.LOGIN_AGAIN.exc()
        # 사용자 검증
        if not await AuthService.check_user(db, name):
            AuthService.clear_cookies(response)
            raise TokenAuth.USER_NOT_FOUND.exc()
        
        access_token = Token.create_access_token(name)
        refresh_token = Token.create_refresh_token(name)
        await AuthService.add_refresh_token(db, refresh_token, name)
        await db.commit()
        AuthService.set_cookies(response, access_token, refresh_token)
        return RenewResponse()
    except SQLAlchemyError:
        await db.rollback()
        raise Server.DB_ERROR.exc()



# --- LogOut API [HTTP POST : https://{ServerDNS}/api/auth/log-out] ---
@router.post("/log-out",
             status_code=status.HTTP_200_OK,
             summary="Log-Out",
             description="사용자의 로그아웃")
async def logout(request: Request, 
                 response: Response, 
                 name: str = Depends(GetCurrentUser),
                 db: AsyncSession = Depends(AsyncDB.get_db)) -> LogOutResponse:
    access_token = request.cookies.get(ACCESS)
    refresh_token = request.cookies.get(REFRESH)
    try:
        await db.begin()
        # 검증
        if not await Token.is_normal_tokens(db, access_token, refresh_token, name):
            raise TokenAuth.TOKEN_INVALID.exc()
        await AuthService.handle_logout_tokens(db, access_token, refresh_token)
        AuthService.clear_cookies(response)
        await db.commit()
        return LogOutResponse()
    except SQLAlchemyError:
        await db.rollback()
        raise Server.DB_ERROR.exc()



# --- 회원탈퇴 API [HTTP DELETE : https://{ServerDNS}/api/auth/withdraw] ---
@router.delete(path="/withdraw",
               status_code=status.HTTP_200_OK,
               summary="Account Withdrawal",
               description="Front 단에서 추가 확인(id 와 pw)을 거쳐 로그인한 사용자의 계정을 영구적으로 삭제")
async def withdraw_user(request: Request, body: WithdrawRequest, response: Response, 
                        name:str = Depends(GetCurrentUser), 
                        db: AsyncSession = Depends(AsyncDB.get_db)) -> WithdrawResponse:
    try:
        await db.begin()
        email = await AuthService.parse_name(db, name)
        if email is None or not await AuthService.withdraw_check_user(db, email, body.email, body.user_pw):
            raise Withdraw.INVALID_FORMAT.exc()
        AuthService.clear_cookies(response)
        await db.commit()
        return WithdrawResponse()
    except SQLAlchemyError:
        await db.rollback()
        raise Server.DB_ERROR.exc()