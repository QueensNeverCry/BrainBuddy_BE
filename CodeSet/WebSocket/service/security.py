from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta
from typing import Literal
import uuid
import logging

from WebSocket.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TYPE, REFRESH_TYPE, ISSUER

from WebSocket.repository import AccessBlackList, RefreshTokensTable
from Application.core.exceptions import TokenAuth, Server


RequiredClaims = {"sub", "jti", "iat", "typ", "iss", "exp"}

# exceptions 작성 완료시 CloseCodes 삭제후 변경할 것
CloseCodes = {"invalid": {"type":    "error",                 
                          "code":    4401,                    
                          "message": "Invalid token"},
              "access_expired": {"type":    "error",
                                 "code":    4402,
                                 "message": "Access token expired"},
              "refresh_expired": {"type":    "error",
                                  "code":    4403,
                                  "message": "Refresh token expired"}}

def get_invalid_claims(payload: dict) -> set[str]:
    # RequiredClaims 에 없는 claim 존재 여부 검사
    extra = set(payload.keys()) - RequiredClaims
    if extra:
        return extra
    # 존재하지 않는 필수 claim , 값이 결측된 claim 검사
    invalid = set()
    for claim in RequiredClaims:
        if claim not in payload:
            invalid.add(claim)
            continue
        value = payload[claim]
        if value is None or (isinstance(value, str) and value.strip() == ""):
            invalid.add(claim)
    return invalid

def check_standard_claims(access_payload: dict, refresh_payload: dict, name: str) -> bool:
    if access_payload.get("sub") != name or refresh_payload.get("sub") != name:
        return False
    if access_payload.get("typ") != ACCESS_TYPE or refresh_payload.get("typ") != REFRESH_TYPE:
        return False
    if access_payload.get("iss") != refresh_payload.get("iss") != ISSUER:
        return False
    return True


class TokenService:
    @staticmethod
    async def verify_tokens(db: AsyncSession, access: str, refresh: str, user_name: str) -> Literal["valid", "access_expired", "refresh_expired", "invalid"]:
        # 1. 위변조 검증
        try:
            access_payload = jwt.decode(access,
                                        JWT_SECRET_KEY,
                                        algorithms=[JWT_ALGORITHM],
                                        options={"verify_exp": False})
            refresh_payload = jwt.decode(refresh,
                                         JWT_SECRET_KEY,
                                         algorithms=[JWT_ALGORITHM],
                                         options={"verify_exp": False})
        except JWTError:
            return "invalid"
        access_invalid = get_invalid_claims(access_payload)
        refresh_invalid = get_invalid_claims(refresh_payload)
        if access_invalid or refresh_invalid:
            return "invalid"
        # 사용자 일치, 표준 claim 확인
        if not check_standard_claims(access_payload, refresh_payload, user_name):
            await AccessBlackList.add_blacklist_token(access_payload.get("jti"), access_payload.get("exp"))
            await RefreshTokensTable.update_to_revoked(db, refresh_payload.get("jti"))
            return "invalid"
        jti = refresh_payload.get("jti")
        # refresh 토큰이 revoked 인 경우
        revoked = await RefreshTokensTable.is_revoked(db, jti)
        if revoked:
            await AccessBlackList.add_blacklist_token(access_payload.get("jti"), access_payload.get("exp"))
            return "invalid"
        # refresh 토큰의 만료된 경우 재로그인 지시.. 근데 그냥 refresh 요청을 하고 그다음에 로그인하게...해야 할듯.. 쿠키비우기 ㅜㅜ
        now = datetime.now(timezone.utc)
        exp_refresh = datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc)
        if exp_refresh < now:
            await RefreshTokensTable.update_to_revoked(db, refresh_payload.get("jti"))
            return "refresh_expired"
        # 만약 access 토큰만 만료된 경우 토큰 재발급 요청 지시 반환
        exp_access = datetime.fromtimestamp(access_payload.get("exp"), tz=timezone.utc)
        if exp_access < now:
            return "access_expired"
        # 사용자 인증 완료
        return "valid"