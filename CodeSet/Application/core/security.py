from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta
import uuid
import logging

from Application.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_SEC, REFRESH_TOKEN_EXPIRE_SEC, ACCESS_TYPE, REFRESH_TYPE, ISSUER

from Application.core.repository import AccessBlackList, RefreshTokensTable
from Application.core.exceptions import TokenAuth, Server


RequiredClaims = {"sub", "jti", "iat", "typ", "iss", "exp"}

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

class Token:
    # JWT ACCESS 토큰 생성
    @staticmethod
    def create_access_token(name: str) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(seconds= ACCESS_TOKEN_EXPIRE_SEC)
        payload = {"iat": int(now.timestamp()),
                   "exp": int(expire.timestamp()),
                   "jti": str(uuid.uuid4()),
                   "sub": name,
                   "typ": ACCESS_TYPE,
                   "iss": ISSUER}
        try:
            access_token = jwt.encode(claims= payload, key= JWT_SECRET_KEY, algorithm= JWT_ALGORITHM)
            return access_token
        except JWTError:
            raise Server.SERVER_ERROR.exc()
        # 예상하지 못한 내부 에러
        except Exception as e:
            logging.error("create_access_token error: %s", e, exc_info=True)
            raise Server.SERVER_ERROR.exc()

    # JWT REFRESH 토큰 생성
    @staticmethod
    def create_refresh_token(name: str) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(seconds= REFRESH_TOKEN_EXPIRE_SEC)
        payload = {"iat": int(now.timestamp()),
                   "exp": int(expire.timestamp()),
                   "jti": str(uuid.uuid4()),
                   "sub": name,
                   "typ": REFRESH_TYPE,
                   "iss": ISSUER}
        try:
            refresh_token = jwt.encode(payload, key= JWT_SECRET_KEY, algorithm= JWT_ALGORITHM)
            return refresh_token
        except JWTError:
            raise TokenAuth.TOKEN_INVALID.exc()
        # 예상하지 못한 내부 에러
        except Exception as e:
            logging.error("create_refresh_token error: %s", e, exc_info=True)
            raise Server.SERVER_ERROR.exc()

    # 두 token 모든 claim 검증, user_id 일치 확인
    @staticmethod
    async def is_normal_tokens(db : AsyncSession, old_access : str, old_refresh : str, name : str | None) -> bool:
        if old_access is None or old_refresh is None or name is None:
            return False
        now = datetime.now(timezone.utc)
        try:
            access_payload = jwt.decode(old_access, JWT_SECRET_KEY, [JWT_ALGORITHM], options={"verify_exp": False})
            refresh_payload = jwt.decode(old_refresh, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
            # claim 검사
            access_invalid = get_invalid_claims(access_payload)
            refresh_invalid = get_invalid_claims(refresh_payload)
            if access_invalid or refresh_invalid:
                return False
            if not check_standard_claims(access_payload, refresh_payload, name):
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
        except Exception as e:
            logging.error("is_refresh_revoked error: %s", e, exc_info=True)
            raise Server.SERVER_ERROR.exc()
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
                raise TokenAuth.TOKEN_INVALID.exc()
            return payload
        except ExpiredSignatureError:
            raise TokenAuth.TOKEN_EXPIRED.exc()
        except JWTError:
            raise TokenAuth.TOKEN_INVALID.exc()
        except Exception as e:
            logging.error("get_payload error: %s", e, exc_info=True)
            raise Server.SERVER_ERROR.exc()

    # JWT 토큰에서 email 추출 (만료시각 검증 X)
    @staticmethod
    def parse_email(token: str) -> str:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, [JWT_ALGORITHM], options={"verify_exp": False})
            return payload.get("sub")
        except JWTError:
            raise TokenAuth.TOKEN_INVALID.exc()
        except Exception as e:
            logging.error("parse_email error: %s", e, exc_info=True)
            raise Server.SERVER_ERROR.exc()
        
    # JWT 토큰에서 jti 추출 (만료시각 검증 X)
    @staticmethod
    def parse_jti(token: str) -> str:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, [JWT_ALGORITHM], options={"verify_exp": False})
            return payload.get("jti")
        except JWTError:
            raise TokenAuth.TOKEN_INVALID.exc()
        except Exception as e:
            logging.error("parse_email error: %s", e, exc_info=True)
            raise Server.SERVER_ERROR.exc()
        
    # JWT 토큰에서 exp 추출 (만료시각 검증 X)
    @staticmethod
    def parse_exp(token: str) -> str:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, [JWT_ALGORITHM], options={"verify_exp": False})
            return payload.get("exp")
        except JWTError:
            raise TokenAuth.TOKEN_INVALID.exc()
        except Exception as e:
            logging.error("parse_email error: %s", e, exc_info=True)
            raise Server.SERVER_ERROR.exc()