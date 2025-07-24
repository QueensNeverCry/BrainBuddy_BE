from fastapi import HTTPException, status
from jose import jwt, JWTError
from datetime import datetime, timezone
import redis

from src.core.config import LOCAL, REDIS_PORT, BLACK_LIST_ID, JWT_SECRET_KEY, JWT_ALGORITHM, EXIST

BlackList = redis.Redis(host= LOCAL, port= REDIS_PORT, db= BLACK_LIST_ID)

# JWT 토큰에서 jti(JWT ID), 만료시각 값을 추출
def parse_token(token: str) -> tuple[str, datetime]:
    try:
        payload = jwt.decode( token,
                              JWT_SECRET_KEY,
                              JWT_ALGORITHM )
        jti = payload.get("jti")
        exp = payload.get("exp")
        # exp는 UNIX timestamp(초) -> datetime 로 타입 변경
        exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
        return jti, exp_dt
    except JWTError as e:
        raise HTTPException( status_code= status.HTTP_401_UNAUTHORIZED,
                             detail= f"유효하지 않은 토큰입니다. {e}" )

# jti(Key)와 만료 시간을 설정 Redis에 저장
def blacklist_token(jti: str, expire: datetime) -> None:
    now = datetime.now(timezone.utc)
    ttl = max(int((expire - now).total_seconds()), 1) # 딱 0이 되어버리면 1로 보정
    BlackList.setex(f"blacklist:{jti}", ttl, EXIST)

# jti 를 이용하여 유효한 토큰인지 검사
def is_token_blacklisted(jti: str) -> bool:
    return BlackList.exists(f"blacklist:{jti}")