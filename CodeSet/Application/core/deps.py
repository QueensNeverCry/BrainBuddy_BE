from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

from Application.core.database import AsyncSessionLocal  # 공통 세션메이커(sessionmaker)

from Application.core.security import Token
from Application.core.exceptions import TokenAuth, Server
from Application.core.config import ACCESS

def GetCurrentUser(request: Request) -> str:
    # ACCESS 토큰 추출
    token = request.cookies.get(ACCESS)
    if not token:
        raise TokenAuth.TOKEN_INVALID.exc()
    try:
        payload = Token.get_payload(token)
        email = payload.get("sub")
        if email is None:
            raise TokenAuth.TOKEN_INVALID.exc()
        return email
    except Exception:
        raise Server.SERVER_ERROR.exc()

class AsyncDB:
    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        async with AsyncSessionLocal() as session:    # 현재 하나의 세션만 사용 ()
            yield session   # context exit 시 자동으로 session.close()
