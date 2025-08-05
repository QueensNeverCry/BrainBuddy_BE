from fastapi import WebSocket, HTTPException, status
from starlette.websockets import WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

from WebSocket.core.database import AsyncSessionLocal  # 공통 세션메이커(sessionmaker)

from WebSocket.core.config import ACCESS, REFRESH

class Get:
    async def AccessToken(websocket: WebSocket) -> str:
        access_token = websocket.cookies.get(ACCESS)
        if not access_token: # 에러 커스텀 할 것
            raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="None Access Token"
        )
        return access_token

    async def RefreshToken(websocket: WebSocket) -> str:
        refresh_token = websocket.cookies.get(REFRESH)
        if not refresh_token: # 에러 커스텀 할 것
            raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="None Refresh Token"
        )
        return refresh_token

    async def UserName(websocket: WebSocket) -> str:
        user_name = websocket.query_params.get("user_name")
        if not user_name: # 에러 커스텀 할 것
            raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="None User Name"
        )
        return user_name

class AsyncDB:
    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        async with AsyncSessionLocal() as session:    # 현재 하나의 세션만 사용 ()
            yield session   # context exit 시 자동으로 session.close()
