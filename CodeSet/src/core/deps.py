from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError, ExpiredSignatureError

from src.models.users import User
from src.core.database import UsersAsyncSession, RefreshTokensAsyncSession, ScoreTablesAsyncSession
from src.core.security import Token
from src.core.response_code import TokenAuth
from src.core.config import ACCESS, REFRESH, JWT_SECRET_KEY, JWT_ALGORITHM

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
    # Users table이 있는 Database Session 반환하는 의존성 함수
    @staticmethod
    def get_users():
        db: AsyncSession = UsersAsyncSession()
        try:
            yield db  # 세션을 호출 함수에 넘김
        finally:
            db.close()  # 작업 끝나면 세션 닫기(메모리/커넥션 누수 방지)

    # RefreshTokens table이 있는 Database Session 반환하는 의존성 함수 (현재 Users table 과 동일 Database 이긴 함..ㅋ)
    @staticmethod
    def get_refresh_tokens():
        db: AsyncSession = RefreshTokensAsyncSession()
        try:
            yield db
        finally:
            db.close()

    # TotalScore, DailyScore table 이 있는 Database Session 반환하는 의존성 함수
    @staticmethod
    def get_score_tables():
        db: AsyncSession = ScoreTablesAsyncSession()
        try:
            yield db
        finally:
            db.close()