from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import uuid
import logging

from WebSocket.core.exceptions import TokenVerdict
from WebSocket.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TYPE, REFRESH_TYPE, ISSUER

from WebSocket.repository import AccessBlackList, RefreshTokensTable


RequiredClaims = {"sub", "jti", "iat", "typ", "iss", "exp"}

def GetInvalidClaims(payload: dict) -> set[str]:
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

# 각 field 의 값 확인
def CheckStandardClaims(access_payload: dict, refresh_payload: dict, name: str) -> bool:
    if access_payload.get("sub") != name or refresh_payload.get("sub") != name:
        return False
    if access_payload.get("typ") != ACCESS_TYPE or refresh_payload.get("typ") != REFRESH_TYPE:
        return False
    if access_payload.get("iss") != ISSUER or refresh_payload.get("iss") != ISSUER:
        return False
    return True


class TokenService:
    @staticmethod
    async def verify_tokens(db: AsyncSession, access: str, refresh: str, user_name: str) -> TokenVerdict:
        # 위변조 검증
        try:
            ap = jwt.decode(token=access,
                            key=JWT_SECRET_KEY,
                            algorithms=[JWT_ALGORITHM],
                            options={"verify_exp": False})
            rp = jwt.decode(token=refresh,
                            key=JWT_SECRET_KEY,
                            algorithms=[JWT_ALGORITHM],
                            options={"verify_exp": False})
        except JWTError:
            return TokenVerdict.INVALID_TOKEN
        access_invalid = GetInvalidClaims(ap)
        refresh_invalid = GetInvalidClaims(rp)
        if access_invalid or refresh_invalid:
            return TokenVerdict.INVALID_TOKEN
        # 사용자 일치, 표준 claim 확인
        if not CheckStandardClaims(ap, rp, user_name):
            async with db.begin():
                await AccessBlackList.add_blacklist_token(ap.get("jti"), ap.get("exp"))
                await RefreshTokensTable.update_to_revoked(db, rp.get("jti"))
            return TokenVerdict.INVALID_TOKEN
        jti = rp.get("jti")
        # refresh 토큰의 만료된 refresh 요청을 하고 그다음에 로그인하게 유도
        now = datetime.now(timezone.utc)
        exp_refresh = datetime.fromtimestamp(rp["exp"], tz=timezone.utc)
        if exp_refresh < now:
            async with db.begin():
                await RefreshTokensTable.update_to_revoked(db, rp.get("jti"))
            return TokenVerdict.REFRESH_TOKEN_EXPIRED
        # 만약 access 토큰만 만료된 경우 토큰 재발급 요청 지시 반환
        exp_access = datetime.fromtimestamp(ap.get("exp"), tz=timezone.utc)
        if exp_access < now:
            return TokenVerdict.ACCESS_TOKEN_EXPIRED
        # refresh 토큰이 revoked 인 경우
        async with db.begin():
            revoked = await RefreshTokensTable.is_revoked(db, jti)
            if revoked:
                await AccessBlackList.add_blacklist_token(ap.get("jti"), ap.get("exp"))
                return TokenVerdict.INVALID_TOKEN
        # access 토큰의 blacklist 검사
        if await AccessBlackList.is_token_blacklisted(ap.get("jti")):
            return TokenVerdict.INVALID_TOKEN
        # 사용자 인증 완료
        print(f"[SECURE] : {user_name} is valid user.")
        return TokenVerdict.VALID