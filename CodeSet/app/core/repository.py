from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import redis.asyncio as aioredis
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from typing import Union

from app.models.security import RefreshToken
from app.core.response_code import TokenAuth
from app.core.config import LOCAL, REDIS_PORT, BLACK_LIST_ID, EXIST


# BlackList = redis.Redis(host= LOCAL, port= REDIS_PORT, db= BLACK_LIST_ID)
BlackList = aioredis.Redis(host=LOCAL, port=REDIS_PORT, db=BLACK_LIST_ID)

class AccessBlackList:
    # jti(Key)와 만료 시간을 설정 Redis에 저장
    @staticmethod
    async def add_blacklist_token(jti: str, expire : Union[int, datetime]) -> None:
        now = datetime.now(timezone.utc)
        if isinstance(expire, (int, float)):
            expire_dt = datetime.fromtimestamp(expire, timezone.utc)
        else:
            expire_dt = expire
        ttl = max(int((expire_dt - now).total_seconds()), 1) # 딱 0이 되어버리면 1로 보정
        await BlackList.setex(jti, ttl, EXIST)

    # jti 를 이용하여 유효한 토큰인지 검사
    @staticmethod
    async def is_token_blacklisted(jti: str) -> bool:
        return await BlackList.exists(jti)

class RefreshTokensTable:
    @staticmethod
    async def update_to_revoked(db : AsyncSession, jti: str) -> None:
        query = (update(RefreshToken).where(RefreshToken.jti == jti)
                                        .values(revoked=True)
                                        .execution_options(synchronize_session="fetch"))
        try:
            await db.execute(query)
            await db.flush()
        except SQLAlchemyError:
            await db.rollback()
            raise HTTPException(status_code=TokenAuth.SERVER_ERROR.value.status,
                                detail={"code": TokenAuth.SERVER_ERROR.value.code,
                                        "message": TokenAuth.SERVER_ERROR.value.message})
        
    @staticmethod
    async def is_revoked(db : AsyncSession, jti: str) -> bool | None:
        try:
            query = select(RefreshToken.revoked).where(RefreshToken.jti == jti)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError:
            raise HTTPException(status_code=TokenAuth.SERVER_ERROR.value.status,
                                detail={"code": TokenAuth.SERVER_ERROR.value.code,
                                        "message": TokenAuth.SERVER_ERROR.value.message})