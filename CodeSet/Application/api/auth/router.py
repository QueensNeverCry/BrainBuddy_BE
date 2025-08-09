from fastapi import APIRouter, Request, Response, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from Application.core.deps import AsyncDB, GetCurrentUser, ParseName
from Application.core.exceptions import Server

from Application.api.auth.service import AuthService, TokenService
from Application.api.auth.exceptions import SignUp, Login, Withdraw
from Application.api.auth.schemas import SignUpRequest, SignUpResponse, LogInRequest, LogInResponse, RenewResponse, LogOutResponse, WithdrawRequest, WithdrawResponse



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
        email = request.email
        user_name = request.user_name
        print(f"[LOG] : {user_name} requested sign - up.")
        # email, user_name 중복 검사
        if await AuthService.check_duplicate(db, email, user_name):
            raise SignUp.USER_EXISTS.exc()
        # 비밀번호 해싱 및 DB 저장
        await AuthService.register_user(db, request)
        return SignUpResponse(user_name=user_name)
    except SQLAlchemyError:
        raise Server.DB_ERROR.exc()
# ----------------------------------------------------------------------


# --- 로그인 API [HTTPS POST : https://{ServerDNS}/api/auth/log-in] ---
@router.post("/log-in", 
             status_code= status.HTTP_200_OK,
             summary= "Log-in", 
             description= "사용자의 ID, PW 를 입력받음")
async def login(request: LogInRequest,
                response: Response,
                db: AsyncSession = Depends(AsyncDB.get_db)) -> LogInResponse:
    try:
        # ID 와 PW 가 일치한 사용자 조회
        user_name = await AuthService.find_user(db, request)
        if user_name == "":
            raise Login.USER_NOT_FOUND.exc()
        # Access / Refresh 토큰 발행
        await TokenService.issue_tokens(db, response, user_name)
        return LogInResponse(user_name=user_name)
    except SQLAlchemyError:
        raise Server.DB_ERROR.exc()
# ---------------------------------------------------------------------


# --- Token 재발급 요청 API [HTTPS POST : https://{ServerDNS}/api/auth/refresh] ---
@router.post("/refresh", 
             status_code= status.HTTP_200_OK,
             summary= "Refresh Tokens", 
             description= "사용자의 Access / Refresh Tokens 를 쿠키를 통해 입력받음")
async def renew_tokens(request: Request,
                       response: Response, 
                       db: AsyncSession = Depends(AsyncDB.get_db),
                       user_name: str = Depends(ParseName)) -> RenewResponse:
    try:
        await TokenService.verify_tokens(db, request, response, user_name)
        await TokenService.issue_tokens(db, response, user_name)
        return RenewResponse()
    except SQLAlchemyError:
        raise Server.DB_ERROR.exc()
# ------------------------------------------------------------------------------


# --- LogOut API [HTTPS POST : https://{ServerDNS}/api/auth/log-out] --------
@router.post("/log-out",
             status_code=status.HTTP_200_OK,
             summary="Log-Out",
             description="사용자의 로그아웃")
async def logout(request: Request, 
                 response: Response, 
                 name: str = Depends(ParseName),
                 db: AsyncSession = Depends(AsyncDB.get_db)) -> LogOutResponse:
    try:
        await TokenService.verify_tokens(db, request, response, name)
        await TokenService.handle_logout_tokens(db, request, response)
        return LogOutResponse()
    except SQLAlchemyError:
        raise Server.DB_ERROR.exc()
# ---------------------------------------------------------------------------


# --- 회원탈퇴 API [HTTPS DELETE : https://{ServerDNS}/api/auth/withdraw] ---
@router.delete(path="/withdraw",
               status_code=status.HTTP_200_OK,
               summary="Account Withdrawal",
               description="Front 단에서 추가 확인(id 와 pw)을 거쳐 로그인한 사용자의 계정을 영구적으로 삭제")
async def withdraw_user(request: Request, 
                        body: WithdrawRequest, 
                        response: Response, 
                        name:str = Depends(GetCurrentUser), 
                        db: AsyncSession = Depends(AsyncDB.get_db)) -> WithdrawResponse:
    try:
        email = await AuthService.parse_email(db, name)
        if not await AuthService.withdraw_check_user(db, email, body.email, body.user_pw):
            raise Withdraw.INVALID_FORMAT.exc()
        await TokenService.handle_logout_tokens(db, request, response)
        return WithdrawResponse()
    except SQLAlchemyError:
        raise Server.DB_ERROR.exc()
# -------------------------------------------------------------------------