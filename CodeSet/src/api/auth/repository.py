from sqlalchemy import select, update, delete, insert, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from datetime import datetime, timezone

from src.models.users import User
from src.models.security import RefreshToken

from src.api.auth.response_code import TokenDB

class Users:
    @staticmethod
    async def exists_user_id(db: AsyncSession, user_id: str) -> bool:
        query = select(exists().where(User.user_id == user_id))
        result = await db.execute(query)
        return result.scalar()
    
    @staticmethod
    async def get_user(db: AsyncSession, user_id: str) -> User | None:
        query = select(User).where(User.user_id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        if user is None:
            return None
        return user
    
    @staticmethod
    async def is_active_user(db: AsyncSession, user_id: str) -> bool:
        query = select(User.status).where(User.user_id == user_id)
        status = await db.scalar(query)  # 없으면 None 반환
        return status == "active"
    
    @staticmethod
    async def delete_user(db: AsyncSession, user_id: str) -> None:
        query = delete(User).where(User.user_id == user_id)
        try:
            await db.execute(query)
            await db.commit()
        except SQLAlchemyError:
            await db.rollback()
            raise HTTPException(status_code=TokenDB.SERVER_ERROR.value.status,
                                detail={"code": TokenDB.SERVER_ERROR.value.code,
                                        "message": TokenDB.SERVER_ERROR.value.message})

class RefreshTokens:
    @staticmethod
    async def purge_user_tokens(db: AsyncSession, user_id: str) -> None:
        now = datetime.now(timezone.utc)
        # DELETE 쿼리: user_id 일치 + (expires_at <= now OR revoked = True)
        query = (delete(RefreshToken).where(RefreshToken.user_id == user_id,  
                                                (RefreshToken.expires_at <= now) | (RefreshToken.revoked == True))
                                           .execution_options(synchronize_session="fetch") )
        try:
            await db.execute(query)
            await db.commit() 
        except SQLAlchemyError:
            await db.rollback()
            raise HTTPException(status_code=TokenDB.SERVER_ERROR.value.status,
                                detail={"code": TokenDB.SERVER_ERROR.value.code,
                                        "message": TokenDB.SERVER_ERROR.value.message})
    
    @staticmethod
    async def update_token(db: AsyncSession, payload: dict, user_id: str) -> bool:
        issued_at_value = payload["iat"]
        if isinstance(issued_at_value, (int, float)):
            issued_at = datetime.fromtimestamp(issued_at_value, timezone.utc)
        else: # 이미 datetime 객체인 경우
            issued_at = issued_at_value 
        expires_at_value = payload["exp"]
        if isinstance(expires_at_value, (int, float)):
            expires_at = datetime.fromtimestamp(expires_at_value, timezone.utc)
        else:
            expires_at = expires_at_value
        query = (update(RefreshToken).where(RefreshToken.jti == payload["jti"])
                                            .values(user_id=user_id,
                                                    issued_at=issued_at,
                                                    expires_at=expires_at,
                                                    revoked=False)
                                            .execution_options(synchronize_session="fetch"))
        try:
            result = await db.execute(query)
            await db.commit()
            return bool(result.rowcount)
        except SQLAlchemyError:
            await db.rollback()
            raise HTTPException(status_code=TokenDB.SERVER_ERROR.value.status,
                                detail={"code": TokenDB.SERVER_ERROR.value.code,
                                        "message": TokenDB.SERVER_ERROR.value.message})
        
    @staticmethod
    async def insert_token(db: AsyncSession, payload: dict, user_id: str) -> None:
        issued_at_value = payload["iat"]
        if isinstance(issued_at_value, (int, float)):
            issued_at = datetime.fromtimestamp(issued_at_value, timezone.utc)
        else: # 이미 datetime 객체인 경우
            issued_at = issued_at_value 
        expires_at_value = payload["exp"]
        if isinstance(expires_at_value, (int, float)):
            expires_at = datetime.fromtimestamp(expires_at_value, timezone.utc)
        else:
            expires_at = expires_at_value
        query = insert(RefreshToken).values(user_id=user_id, 
                                                jti=payload["jti"],
                                                issued_at=issued_at,
                                                expires_at=expires_at,
                                                revoked=False)
        # 실행(execute) 및 커밋(commit)
        try:
            await db.execute(query)
            await db.commit()
        except SQLAlchemyError:
            await db.rollback()
            raise HTTPException(status_code=TokenDB.SERVER_ERROR.value.status,
                                detail={"code": TokenDB.SERVER_ERROR.value.code,
                                        "message": TokenDB.SERVER_ERROR.value.message})