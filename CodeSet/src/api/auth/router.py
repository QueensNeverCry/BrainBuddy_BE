from fastapi import APIRouter, Request, Response, HTTPException, Depends, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import Token
from src.core.deps import AsyncDB, GetCurrentUser
from src.core.config import ACCESS, REFRESH

from src.api.auth.schemas import SignUpRequest, SignUpResponse, LogInRequest, LogInResponse, RenewResponse, LogOutResponse, WithdrawReq, WithdrawRes
from src.api.auth.response_code import SignUpCode, LogInCode, TokenAuth, WithdrawCode
from src.api.auth.service import AuthService
from src.api.auth.utils import get_code_info



router = APIRouter()



# pydantic 의 모델 단 에서 먼저 Error 처리
@router.exception_handler(RequestValidationError)
async def auth_validation_handler(request: Request, 
                                  exc: RequestValidationError):
    # 에러 code에 따라 SignUpCode Enum에서 정보를 추출
    for error in exc.errors():
        code = error.get("msg")
        code_info = get_code_info(code)
        if code_info:
            return JSONResponse(status_code=code_info.status,
                                content={"status": "fail",
                                         "code": code_info.code, 
                                         "message": code_info.message})
    # 기타 예외
    return JSONResponse(status_code=status.HTTP_418_IM_A_TEAPOT,
                        content={"status": "fail",
                                 "code": "INVALID_REQ",
                                 "message": str(object=exc.errors())})



# 회원가입 API [HTTPS POST : https://{ServerDNS}/api/auth/sign-up]
@router.post("/auth/sign-up",
             status.HTTP_201_CREATED,
             summary="Sign Up",
             description="신규 사용자 회원가입 API. 이름, ID, PW 를 입력받음")
async def sign_up(request: SignUpRequest, 
                  users_db: AsyncSession = Depends(AsyncDB.get_users),
                  score_db: AsyncSession = Depends(AsyncDB.get_score_tables)) -> SignUpResponse:
    # 필드의 존재 여부, 형식 검사, pw 와 pw_confirm 확인은 pydantic model 단에서 완료 -> user_id 의 중복 확인만 수행
    email = request.email
    user_name = request.user_name
    if await AuthService.check_duplicate(users_db, email, user_name):
        raise HTTPException(SignUpCode.USER_EXISTS.value.status,
                            detail={"code": SignUpCode.USER_EXISTS.value.code,
                                    "message": SignUpCode.USER_EXISTS.value.message})
    # 비밀번호 해싱 및 DB 저장
    user = await AuthService.register_user(users_db, score_db, request)
    # api response
    return SignUpResponse(status="success",
                          user_name=user.user_name,
                          message=SignUpCode.CREATED.value.message,
                          code=SignUpCode.CREATED.value.code)



# 로그인 API [HTTP POST : https://{ServerDNS}/api/auth/log-in]
@router.post("/auth/log-in", 
             status_code= status.HTTP_200_OK,
             summary= "Log-in", 
             description= "사용자의 ID, PW 를 입력받음")
async def login(request: LogInRequest, response: Response, 
                users: AsyncSession = Depends(AsyncDB.get_users), 
                tokens: AsyncSession = Depends(AsyncDB.get_refresh_tokens)) -> LogInResponse | JSONResponse:
    # ID 와 PW 가 일치한 사용자 조회
    user = await AuthService.find_user(users, request=request)
    if not user:
        raise HTTPException(status_code=LogInCode.USER_NOT_FOUND.value.status,
                            detail={"code": LogInCode.USER_NOT_FOUND.value.code,
                                    "message": LogInCode.USER_NOT_FOUND.value.message})
    access_token = Token.create_access_token(user.email)
    refresh_token = Token.create_refresh_token( user.email)
    await AuthService.add_refresh_token(tokens, refresh_token, user.email)
    # response - cookie에 JWT ACCESS TOKEN 설정
    AuthService.set_cookies(response, access_token, refresh_token)
    return LogInResponse(status= "success",
                         user_name= user.user_name,
                         user_id= user.user_id,
                         code= LogInCode.LOGIN_SUCCESS.value.code,
                         message= LogInCode.LOGIN_SUCCESS.value.message)



# JWT Token 재발급 요청 API [HTTP POST : https://{ServerDNS}/api/auth/refresh]
@router.post("/auth/refresh", 
             status_code= status.HTTP_200_OK,
             summary= "Refresh Tokens", 
             description= "사용자의 Access / Refresh Tokens 를 쿠키를 통해 입력받음")
async def renew_tokens(request: Request, response: Response, 
                       db: AsyncSession = Depends(AsyncDB.get_refresh_tokens), 
                       email: str = Depends(GetCurrentUser)) -> RenewResponse:
    old_access_token = request.cookies.get(ACCESS)
    old_refresh_token = request.cookies.get(REFRESH)
    # 두 token 모두 존재, 모든 claim 검증, user_id 일치 확인
    if not await Token.is_normal_tokens(db, old_access_token, old_refresh_token, email=email):
        raise HTTPException(status_code=TokenAuth.TOKEN_INVALID.value.status,
                                    detail={"code" : TokenAuth.TOKEN_INVALID.value.code,
                                            "message" : TokenAuth.TOKEN_INVALID.value.message})
    # Refresh 토큰의 만료 여부 확인
    if Token.is_refresh_expired(db, old_refresh_token):
        raise HTTPException(status_code=TokenAuth.LOGIN_AGAIN.value.status,
                            detail={"code": TokenAuth.LOGIN_AGAIN.value.code,
                                    "message": TokenAuth.LOGIN_AGAIN.value.message})
    # Refresh 토큰의 revoked 여부 확인
    if await Token.is_refresh_revoked(db, old_access_token, old_refresh_token):
        raise HTTPException(status_code=TokenAuth.TOKEN_INVALID.value.status,
                                    detail={"code" : TokenAuth.TOKEN_INVALID.value.code,
                                            "message" : TokenAuth.TOKEN_INVALID.value.message})
    # 사용자 검증
    if not await AuthService.check_user(db, email):
        raise HTTPException(TokenAuth.USER_NOT_FOUND.value.status,
                            detail={"code": TokenAuth.USER_NOT_FOUND.value.code,
                                    "message": TokenAuth.USER_NOT_FOUND.value.message})
    access_token = Token.create_access_token(email)
    refresh_token = Token.create_refresh_token(email)
    await AuthService.add_refresh_token(db, refresh_token, email)
    AuthService.set_cookies(response, access_token, refresh_token)
    return RenewResponse(status="success",
                         code= TokenAuth.REFRESHED.value.code,
                         message= TokenAuth.REFRESHED.value.message)



# LogOut API [HTTP POST : https://{ServerDNS}/api/auth/log-out]
@router.post("/auth/log-out",
             status_code=status.HTTP_200_OK,
             summary="Log-Out",
             description="사용자의 로그아웃")
async def logout(request: Request, response: Response, 
                 db: AsyncSession = Depends(AsyncDB.get_refresh_tokens)) -> LogOutResponse:
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    email = Token.parse_email(access_token)
    # 검증
    if not await Token.is_normal_tokens(db, access_token, refresh_token, email):
        raise HTTPException(status_code=TokenAuth.TOKEN_INVALID.value.status,
                            detail={"code" : TokenAuth.TOKEN_INVALID.value.code,
                                    "message" : TokenAuth.TOKEN_INVALID.value.message})
    await AuthService.handle_logout_tokens(db, access_token, refresh_token)
    # 쿠키 삭제
    AuthService.clear_cookies(response)
    return LogOutResponse(status="success",
                          code="LOGOUT",
                          message="You have been logged out successfully.")



# 회원탈퇴 API [HTTP DELETE : https://{ServerDNS}/api/auth/withdraw]
@router.delete(path="/auth/withdraw",
               status_code=status.HTTP_200_OK,
               summary="Account Withdrawal",
               description="Front 단에서 추가 확인(id 와 pw)을 거쳐 로그인한 사용자의 계정을 영구적으로 삭제")
async def withdraw_user(request: Request, body: WithdrawReq, response: Response, 
                        email:str = Depends(GetCurrentUser), 
                        db: AsyncSession = Depends(AsyncDB.get_users)) -> WithdrawRes:
    if not await AuthService.withdraw_check_user(db, email, WithdrawReq.email, WithdrawReq.user_pw):
        raise HTTPException(status_code=WithdrawCode.INVALID_FORMAT.value.status,
                            detail={"code" : WithdrawCode.INVALID_FORMAT.value.code,
                                    "message" : WithdrawCode.INVALID_FORMAT.value.message})
    AuthService.clear_cookies(response)
    return WithdrawRes(status="success",
                       code=WithdrawCode.WITHDRAW.value.code,
                       message=WithdrawCode.WITHDRAW.value.message)