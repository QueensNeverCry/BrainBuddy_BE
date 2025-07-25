from fastapi import Request, Response
from jose import jwt
from datetime import datetime, timezone

from src.core.security import create_access_token, get_payload
from src.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, SAFE_SEC, ACCESS, REFRESH, ACCESS_TOKEN_EXPIRE_SEC

class PreemptiveTokenRefreshMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive=receive)
            response = Response()
            access_token = request.cookies.get(ACCESS)
            refresh_token = request.cookies.get(REFRESH)
            # 토큰이 존재하면 만료 임박 체크
            if access_token and refresh_token:
                try:
                    payload = jwt.decode(access_token, JWT_SECRET_KEY, algorithms=JWT_ALGORITHM)
                    exp = payload["exp"]
                    now = datetime.now(timezone.utc).timestamp()
                    remain_sec = exp - now
                    if 0 < remain_sec < SAFE_SEC:
                        # 만료 임박시 새 Access Token 발급
                        refresh_payload = get_payload(refresh_token)
                        user_id = refresh_payload["user_id"]
                        new_access_token = create_access_token({"user_id": user_id})
                        response.set_cookie( key= ACCESS,
                                             value= new_access_token,
                                             httponly= True,
                                             secure= True,
                                             samesite= "strict",
                                             max_age= ACCESS_TOKEN_EXPIRE_SEC,
                                             path= "/" )
                except Exception as e:
                    pass  # 토큰 decode 실패 시 무시(401, 403 등등.. 은 개별 라우터에서 처리)
            await self.app(scope, receive, send)
        else:
            await self.app(scope, receive, send)