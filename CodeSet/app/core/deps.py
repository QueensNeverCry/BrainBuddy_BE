from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError, ExpiredSignatureError
from typing import AsyncGenerator

from app.models.users import User
from app.core.database import AsyncSessionLocal  # 공통 세션메이커(sessionmaker)
# from app.core.database import UsersAsyncSession, RefreshTokensAsyncSession, ScoreTablesAsyncSession
from app.core.security import Token
from app.core.response_code import TokenAuth
from app.core.config import ACCESS

def GetCurrentUser(request: Request) -> str:
    # ACCESS 토큰 추출
    token = request.cookies.get(ACCESS)
    if not token:
        raise HTTPException(status_code=TokenAuth.TOKEN_INVALID.value.status,
                            detail={"code": TokenAuth.TOKEN_INVALID.value.code,
                                    "message": TokenAuth.TOKEN_INVALID.value.message})
    try:
        payload = Token.get_payload(token)
        email = payload.get("sub")
        if email is None:
            raise JWTError
        return email
    except JWTError:
        raise HTTPException(status_code=TokenAuth.TOKEN_INVALID.value.status,
                            detail={"code": TokenAuth.TOKEN_INVALID.value.code,
                                    "message": TokenAuth.TOKEN_INVALID.value.message})

class AsyncDB:
    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        async with AsyncSessionLocal() as session:    # 현재 하나의 세션만 사용 ()
            yield session   # context exit 시 자동으로 session.close()

    # # Users table이 있는 Database Session 반환하는 의존성 함수
    # @staticmethod
    # async def get_users():
    #     db: AsyncSession = UsersAsyncSession()
    #     try:
    #         yield db  # 세션을 호출 함수에 넘김
    #     finally:
    #         await db.close()

    # # RefreshTokens table이 있는 Database Session 반환하는 의존성 함수 (현재 Users table 과 동일 Database 이긴 함..ㅋ)
    # @staticmethod
    # async def get_refresh_tokens():
    #     db: AsyncSession = RefreshTokensAsyncSession()
    #     try:
    #         yield db
    #     finally:
    #         await db.close()

    # # TotalScore, DailyScore table 이 있는 Database Session 반환하는 의존성 함수
    # @staticmethod
    # async def get_score_tables():
    #     db: AsyncSession = ScoreTablesAsyncSession()
    #     try:
    #         yield db
    #     finally:
    #         await db.close()