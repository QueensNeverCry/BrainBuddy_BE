from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt

from Application.core.security import Token
from Application.core.repository import AccessBlackList, RefreshTokensTable
from Application.models.users import User
from Application.models.score import TotalScore
from Application.core.config import ACCESS, ACCESS_TOKEN_EXPIRE_SEC, REFRESH, REFRESH_TOKEN_EXPIRE_SEC

from Application.api.auth.schemas import SignUpRequest, LogInRequest
from Application.api.auth.repository import Users, RefreshTokens, TotalScoreDB

class AuthService:
    @staticmethod
    async def check_duplicate(db: AsyncSession, email: str, user_name: str) -> bool:
        return (await Users.exists_user_email(db, email)) or (await Users.exists_user_name(db, user_name))
    
    @staticmethod
    async def register_user(db: AsyncSession, req: SignUpRequest) -> None:
        # plain PW → Hashing
        hashed_pw = bcrypt.hashpw(req.user_pw.encode(), bcrypt.gensalt()).decode()
        req.user_pw = req.user_pw_confirm = None
        # DB 저장 - Users 테이블
        await Users.register_user(db, User(email=req.email,user_name=req.user_name,user_pw=hashed_pw))
        # DB 저장 - Score 테이블
        await TotalScoreDB.register_user(db, TotalScore(user_name=req.user_name))
        
    @staticmethod
    async def find_user(db: AsyncSession, request: LogInRequest) -> User | None:
        user = await Users.get_user(db, request.email)
        if not user:
            return None
        if bcrypt.checkpw(request.user_pw.encode(), user.user_pw.encode()):
            return user
        else:
            return None
    
    @staticmethod
    async def check_user(db: AsyncSession, email: str) -> bool:
        res1 = await Users.exists_user_email(db, email)
        res2 = await Users.is_active_user(db, email)
        return res1 and res2

    @staticmethod
    async def add_refresh_token(db: AsyncSession, refresh_token: str, email: str) -> None:
        # 새 토큰 정보 추출
        payload = Token.get_payload(refresh_token)
        # 해당 사용자의 만료(expired) 또는 폐기(revoked) 토큰 먼저 삭제
        await RefreshTokens.purge_user_tokens(db, email)
        # 동일 jti 토큰이 있으면 update, 없다면 insert (신규 추가)
        if not await RefreshTokens.update_token(db, payload, email):
            await RefreshTokens.insert_token(db, payload, email)
    
    @staticmethod
    def set_cookies(response: Response, access_token: str, refresh_token: str) -> None:
        response.set_cookie(key= ACCESS,
                            value= access_token,
                            httponly= True,     # JS로 접근 불가, XSS 공격 방지
                            secure= True,       # HTTPS에서만 전송 허용
                            samesite= "strict", # CSRF 공격 방지, BrainBuddy 도메인에서 출발한 요청에만 브라우저가 쿠키 첨부 !
                            max_age= ACCESS_TOKEN_EXPIRE_SEC,
                            path= "/")
        response.set_cookie(key= REFRESH,
                            value= refresh_token,
                            httponly= True,
                            secure= True,
                            samesite= "strict",
                            max_age= REFRESH_TOKEN_EXPIRE_SEC,
                            path= "/")
        
    @staticmethod
    async def handle_logout_tokens(db: AsyncSession, access: str, refresh: str) -> None:
        RefreshTokensTable.update_to_revoked(db, Token.parse_jti(refresh))
        AccessBlackList.add_blacklist_token(Token.parse_jti(access), Token.parse_exp(access))

    @staticmethod
    async def withdraw_check_user(db: AsyncSession, email: str, __email: str, pw: str) -> bool:
        if email != __email:
            return False
        # email, pw 검증
        user = await Users.get_user(db, email)
        if not user:
            return False
        if not await Users.is_active_user(db, email):
            return False
        if not bcrypt.checkpw(pw.encode(), user.user_pw.encode()):
            return False
        # Score 테이블에서 해당 사용자의 모든 기록 삭제
        await TotalScoreDB.delete_user(db, user.user_name)
        # Users 테이블에서 해당 사용자 삭제
        await Users.delete_user(db, email)
        return True
    
    @staticmethod
    def clear_cookies(response: Response) -> None:
        response.delete_cookie(key= ACCESS, path="/")
        response.delete_cookie(key= REFRESH, path="/")