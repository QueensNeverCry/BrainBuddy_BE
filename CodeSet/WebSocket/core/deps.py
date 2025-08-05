from fastapi import WebSocket, WebSocketException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator, Dict, Set

from WebSocket.core.database import AsyncSessionLocal  # 공통 세션메이커(sessionmaker)

from WebSocket.core.config import ACCESS, REFRESH

Required: Set[str] = {"user_name", "subject", "location", ACCESS, REFRESH}

class Get:
    @staticmethod
    def Parameters(websocket: WebSocket) -> Dict:
        params: Dict[str, str] = {}
        seen: Set[str] = set()
        for key, value in websocket.query_params.items():
            if key in Required:
                params[key] = value
                seen.add(key)
            else:
                # 허용되지 않은 파라미터 발견 시 즉시 거부
                raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
        # 빠진 필수 파라미터 검사
        missing = Required - seen
        if missing:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
        return params
        

    # @staticmethod
    # async def AccessToken(websocket: WebSocket) -> str:
    #     access_token = websocket.cookies.get(ACCESS)
    #     if not access_token:
    #         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
    #                             detail="None Access Token")
    #     return access_token

    # @staticmethod
    # async def RefreshToken(websocket: WebSocket) -> str:
    #     refresh_token = websocket.cookies.get(REFRESH)
    #     if not refresh_token:
    #         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
    #                             detail="None Refresh Token")
    #     return refresh_token

    # @staticmethod
    # async def UserName(websocket: WebSocket) -> str:
    #     user_name = websocket.query_params.get("user_name")
    #     if not user_name:
    #         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
    #                             detail="None User Name")
    #     return user_name

class AsyncDB:
    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        async with AsyncSessionLocal() as session:    # 현재 하나의 세션만 사용 ()
            yield session   # context exit 시 자동으로 session.close()
