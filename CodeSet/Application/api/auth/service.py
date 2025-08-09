from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import SecretStr
import bcrypt
import asyncio

from Application.core.security import Token
from Application.core.repository import AccessBlackList, RefreshTokensTable
from Application.core.config import ACCESS, ACCESS_TOKEN_EXPIRE_SEC, REFRESH, REFRESH_TOKEN_EXPIRE_SEC
from Application.models.users import User
from Application.models.score import TotalScore

from Application.api.auth.schemas import SignUpRequest, LogInRequest
from Application.api.auth.exceptions import SignUp
from Application.api.auth.repository import UsersDB, RefreshTokensDB, TotalScoreDB, DailyDB



def InsertTokens(res: Response, access_token: str, refresh_token: str) -> None:
    res.set_cookie(key= ACCESS,
                   value= access_token,
                   httponly= True,     # JS로 접근 불가, XSS 공격 방지
                   secure= True,       # HTTPS에서만 전송 허용
                   samesite= "strict", # CSRF 공격 방지, BrainBuddy 도메인에서 출발한 요청에만 브라우저가 쿠키 첨부 !
                   max_age= ACCESS_TOKEN_EXPIRE_SEC,
                   path= "/")
    res.set_cookie(key= REFRESH,
                   value= refresh_token,
                   httponly= True,
                   secure= True,
                   samesite= "strict",
                   max_age= REFRESH_TOKEN_EXPIRE_SEC,
                   path= "/")
    
def ClearCookie(res: Response) -> None:
    res.delete_cookie(key= ACCESS, path="/")
    res.delete_cookie(key= REFRESH, path="/")



class AuthService:
    # READ-ONLY process
    # email 또는 user_name 이 일치한 사용자 확인
    @staticmethod
    async def check_duplicate(db: AsyncSession, email: str, user_name: str) -> bool:
        return UsersDB.exist_user(db=db, email=email, user_name=user_name)
    
    # WRITE process
    # 회원가입을 요청한 사용자의 정보 DB 추가
    @staticmethod
    async def register_user(db: AsyncSession, req: SignUpRequest) -> None:
        pw: str = req.user_pw.get_secret_value()
        hashed_bytes = await asyncio.to_thread(bcrypt.hashpw, pw.encode("utf-8"), bcrypt.gensalt())
        hashed_pw = hashed_bytes.decode("utf-8")
        del pw
        async with db.begin():
            await UsersDB.register_user(db, User(email=req.email,user_name=req.user_name,user_pw=hashed_pw))
            await db.flush()
            await TotalScoreDB.register_user(db, TotalScore(user_name=req.user_name))

    # READ-ONLY process
    # Users 테이블에서 해당 email 을 가진 record 조회 후, 접속자 인증        
    @staticmethod
    async def find_user(db: AsyncSession, req: LogInRequest) -> str:
        user = await UsersDB.get_user(db, req.email)
        if not user:
            return ""
        valid = await asyncio.to_thread(bcrypt.checkpw,
                                           req.user_pw.get_secret_value().encode("utf-8"),
                                           user.user_pw.encode("utf-8"))
        if not valid:
            return ""
        return user.user_name
        
    # READ-ONLY process
    # Users 테이블에서 해당 user_name 을 가진 record 의 email
    @staticmethod
    async def parse_email(db: AsyncSession, user_name: str) -> str | None:
        return await UsersDB.get_email_by_name(db, user_name)

    # WRITE process
    # 회원탈퇴 신청한 사용자 검사 후 table 에서 모든 기록 삭제
    @staticmethod
    async def withdraw_check_user(db: AsyncSession, email: str, __email: str, pw: SecretStr) -> bool:
        if email is None or email != __email:
            return False
        # email, pw 검증
        user = await UsersDB.get_user(db, email)
        if not user:
            return False
        if not await UsersDB.is_active_user(db, email):
            return False
        valid = await asyncio.to_thread(bcrypt.checkpw,
                                           pw.get_secret_value().encode("utf-8"),
                                           user.user_pw.encode("utf-8"))
        if not valid:
            return False
        # Score, Daily, Users 테이블에서 해당 사용자의 모든 기록 삭제
        async with db.begin():
            await TotalScoreDB.delete_user(db, user.user_name)
            await DailyDB.delete_records(db, user.user_name)
            await UsersDB.delete_user(db, email)
        return True



class TokenService:
    # WRITE process
    # 사용자에게 JWT Token 발행
    @staticmethod
    async def issue_tokens(db: AsyncSession, res: Response, user_name: str) -> None:
        # 토큰 발행
        access, refresh, refresh_payload = Token.create_tokens(user_name)
        # 토큰 쿠키 삽입
        InsertTokens(res, access, refresh)
        # RTR 저장
        async with db.begin():
            await RefreshTokensDB.purge_user_tokens(db, user_name) # 만료, 폐기 토큰 삭제
            await RefreshTokensDB.insert_token(db, refresh_payload, user_name)

    # WRITE process
    # 사용자의 Access / Refresh 토큰 검증
    @staticmethod
    async def verify_tokens(db: AsyncSession, req: Request, res: Response, user_name: str) -> None:
        old_access = req.cookies.get(ACCESS)
        old_refresh = req.cookies.get(REFRESH)
        try:
            # 두 token 모두 존재, 모든 claim 검증, user_email 일치 확인
            await Token.check_tokens(db, old_access, old_refresh, user_name)
            # Refresh 토큰의 revoked 여부 확인
            await Token.check_refresh_revoked(db, old_access, old_refresh)
            # Refresh 토큰의 만료 여부 확인
            Token.check_refresh_expired(old_refresh)
            # 사용자 검증
            if not await UsersDB.is_valid_user(db, user_name):
                raise SignUp.FORBIDDEN.exc()
        except:
            ClearCookie(res)
            raise

    # WRITE process
    # 로그아웃 한 사용자의 토큰 revoke
    @staticmethod
    async def handle_logout_tokens(db: AsyncSession, req: Request, res: Response) -> None:
        access = req.cookies.get(ACCESS)
        refresh = req.cookies.get(REFRESH)
        async with db.begin():
            await RefreshTokensTable.update_to_revoked(db, Token.parse_jti(refresh))
        await AccessBlackList.add_blacklist_token(Token.parse_jti(access), Token.parse_exp(access))
        ClearCookie(res)