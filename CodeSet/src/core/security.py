from fastapi import HTTPException, status
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta
import uuid

from src.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_SEC, REFRESH_TOKEN_EXPIRE_SEC, ACCESS_TYPE, REFRESH_TYPE, ISSUER
from src.core.response_code import TokenAuth
from src.core.repository import AccessBlackList, RefreshTokensTable


RequiredClaims = {"sub", "jti", "iat", "typ", "iss", "exp"}

def get_invalid_claims(payload: dict) -> set[str]:
    invalid = set()
    for claim in RequiredClaims:
        # 키가 없거나
        if claim not in payload:
            invalid.add(claim)
            continue
        # 값이 None 또는 빈 문자열
        value = payload[claim]
        if value is None or (isinstance(value, str) and value.strip() == ""):
            invalid.add(claim)
    return invalid


class Token:
    # JWT ACCESS 토큰 생성
    @staticmethod
    def create_access_token(email: str) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(seconds= ACCESS_TOKEN_EXPIRE_SEC)
        payload = {"iat": int(now.timestamp()),
                   "exp": int(expire.timestamp()),
                   "jti": str(uuid.uuid4()),
                   "sub": email,
                   "typ": ACCESS_TYPE,
                   "iss": ISSUER}
        try:
            access_token = jwt.encode(claims= payload, key= JWT_SECRET_KEY, algorithm= JWT_ALGORITHM)
            return access_token
        except JWTError as e:
            raise HTTPException(status_code= TokenAuth.SERVER_ERROR.value.status,
                                detail={"code" : TokenAuth.SERVER_ERROR.value.code,
                                        "message" : TokenAuth.SERVER_ERROR.value.message})

    # JWT REFRESH 토큰 생성
    @staticmethod
    def create_refresh_token(email: str) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(seconds= REFRESH_TOKEN_EXPIRE_SEC)
        payload = {"iat": int(now.timestamp()),
                   "exp": int(expire.timestamp()),
                   "jti": str(uuid.uuid4()),
                   "sub": email,
                   "typ": REFRESH_TYPE,
                   "iss": ISSUER}
        try:
            refresh_token = jwt.encode(payload, key= JWT_SECRET_KEY, algorithm= JWT_ALGORITHM)
            return refresh_token
        except JWTError as e:
            raise HTTPException(status_code= TokenAuth.SERVER_ERROR.value.status,
                                detail={"code" : TokenAuth.SERVER_ERROR.value.code,
                                        "message" : TokenAuth.SERVER_ERROR.value.message})

    # 두 token 모든 claim 검증, user_id 일치 확인
    @staticmethod
    async def is_normal_tokens(db : AsyncSession, old_access : str, old_refresh : str, email : str | None) -> bool:
        if old_access is None or old_refresh is None or email is None:
            return False
        now = datetime.now(timezone.utc)
        try:
            access_payload = jwt.decode(old_access, JWT_SECRET_KEY, [JWT_ALGORITHM], options={"verify_exp": False})
            refresh_payload = jwt.decode(old_refresh, JWT_SECRET_KEY, [JWT_ALGORITHM], options={"verify_exp": False})
            access_invalid = get_invalid_claims(access_payload)
            refresh_invalid = get_invalid_claims(refresh_payload)
            if access_invalid or refresh_invalid:
                return False
            if email != access_payload.get("sub") != refresh_payload.get("sub") or access_payload.get("typ") != ACCESS_TYPE or refresh_payload.get("typ") != REFRESH_TYPE:
                #  Access 는 blacklist 에 등록, Refresh 토큰은 해당 record 가 있다면, revoked = True 설정
                await AccessBlackList.add_blacklist_token(access_payload.get("jti"), access_payload.get("exp"))
                await RefreshTokensTable.update_to_revoked(db, refresh_payload.get("jti"))
                return False
        except:
            return False
        return True
    
    # refresh token 의 만료 여부 확인 (True면 만료(expired) 상태)
    @staticmethod
    def is_refresh_expired(old_refresh : str) -> bool:
        try:
            refresh_payload = jwt.decode(old_refresh, JWT_SECRET_KEY, [JWT_ALGORITHM])
        except ExpiredSignatureError:
            return True
        return False
    
    # refresh token 의 DB table.revoked 속성 확인 (revoked 처리 까지)
    @staticmethod
    async def is_refresh_revoked(db : AsyncSession, old_access_token : str, old_refresh_token : str) -> bool:
        # Refresh Token 을 DB table 에서 jti 기반 조회... revoked 인 경우 Access 는 blacklist 에 등록 후 False 반환
        try:
            refresh_payload = jwt.decode(old_refresh_token,JWT_SECRET_KEY,algorithms=[JWT_ALGORITHM])
        except JWTError:
            return True    
        jti = refresh_payload.get("jti")
        # DB 조회: 해당 JTI의 revoked 플래그 검사
        result = await RefreshTokensTable.is_revoked(db, jti)
        if result is not False:
            access_payload = jwt.decode(old_access_token, JWT_SECRET_KEY, [JWT_ALGORITHM], options={"verify_exp": False})
            await AccessBlackList.add_blacklist_token(access_payload.get("jti"), access_payload.get("exp"))
            return True
        else:
            # 해당 refresh token record 의 revoked = True 처리
            await RefreshTokensTable.update_to_revoked(db, jti)
            return False
    
    # JWT 토큰에서 payload 추출
    @staticmethod
    def get_payload(token: str) -> dict:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, [JWT_ALGORITHM])
            invalid_claims = get_invalid_claims(payload=payload)
            if invalid_claims:
                raise HTTPException(status_code=TokenAuth.TOKEN_INVALID.value.status,
                                    detail={"code" : TokenAuth.TOKEN_INVALID.value.code,
                                            "message" : TokenAuth.TOKEN_INVALID.value.message})
            return payload
        except ExpiredSignatureError:
            raise HTTPException(status_code= TokenAuth.TOKEN_EXPIRED.value.status,
                                detail={"code" : TokenAuth.TOKEN_EXPIRED.value.code,
                                        "message" : TokenAuth.TOKEN_EXPIRED.value.message})
        except JWTError:
            raise HTTPException(status_code= TokenAuth.TOKEN_INVALID.value.status,
                                detail={"code" : TokenAuth.TOKEN_INVALID.value.code,
                                        "message" : TokenAuth.TOKEN_INVALID.value.message})

    # JWT 토큰에서 email 추출 (만료시각 검증 X)
    @staticmethod
    def parse_email(token: str) -> str:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, [JWT_ALGORITHM], options={"verify_exp": False})
            return payload.get("sub")
        except:
            raise HTTPException(status_code= TokenAuth.TOKEN_INVALID.value.status,
                                detail={"code" : TokenAuth.TOKEN_INVALID.value.code,
                                        "message" : TokenAuth.TOKEN_INVALID.value.message})
        
    # JWT 토큰에서 jti 추출 (만료시각 검증 X)
    @staticmethod
    def parse_jti(token: str) -> str:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, [JWT_ALGORITHM], options={"verify_exp": False})
            return payload.get("jti")
        except:
            raise HTTPException(status_code= TokenAuth.TOKEN_INVALID.value.status,
                                detail={"code" : TokenAuth.TOKEN_INVALID.value.code,
                                        "message" : TokenAuth.TOKEN_INVALID.value.message})
        
    # JWT 토큰에서 exp 추출 (만료시각 검증 X)
    @staticmethod
    def parse_exp(token: str) -> str:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, [JWT_ALGORITHM], options={"verify_exp": False})
            return payload.get("exp")
        except:
            raise HTTPException(status_code= TokenAuth.TOKEN_INVALID.value.status,
                                detail={"code" : TokenAuth.TOKEN_INVALID.value.code,
                                        "message" : TokenAuth.TOKEN_INVALID.value.message})