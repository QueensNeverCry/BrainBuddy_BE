from sqlalchemy import select, update, delete, insert, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from datetime import datetime, timezone
import logging

from src.models.users import User
from src.models.score import TotalScore
from src.models.security import RefreshToken

from src.api.auth.response_code import TokenDB

class Users:
    @staticmethod
    async def exists_user_email(db: AsyncSession, email: str) -> bool:
        query = select(exists().where(User.email == email))
        result = await db.execute(query)
        return result.scalar()
    
    @staticmethod
    async def exists_user_name(db: AsyncSession, user_name: str) -> bool:
        query = select(exists().where(User.user_name == user_name))
        result = await db.execute(query)
        return result.scalar()
    
    @staticmethod
    async def get_user(db: AsyncSession, email: str) -> User | None:
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        if user is None:
            return None
        return user
    
    @staticmethod
    async def register_user(db: AsyncSession, user: User) -> None:
        db.add(user)
        await db.flush()
        await db.refresh(user)
    
    @staticmethod
    async def is_active_user(db: AsyncSession, email: str) -> bool:
        query = select(User.status).where(User.email == email)
        status = await db.scalar(query)  # 없으면 None 반환
        return status == "active"
    
    @staticmethod
    async def delete_user(db: AsyncSession, email: str) -> None:
        query = delete(User).where(User.email == email)
        try:
            await db.execute(query)
            await db.flush()
        except SQLAlchemyError:
            await db.rollback()
            raise HTTPException(status_code=TokenDB.SERVER_ERROR.value.status,
                                detail={"code": TokenDB.SERVER_ERROR.value.code,
                                        "message": TokenDB.SERVER_ERROR.value.message})

class RefreshTokens:
    @staticmethod
    async def purge_user_tokens(db: AsyncSession, email: str) -> None:
        now = datetime.now(timezone.utc)
        # DELETE 쿼리: user_id 일치 + (expires_at <= now OR revoked = True)
        query = (delete(RefreshToken).where(RefreshToken.email == email,  
                                                (RefreshToken.expires_at <= now) | (RefreshToken.revoked == True))
                                           .execution_options(synchronize_session="fetch") )
        try:
            await db.execute(query)
        except SQLAlchemyError as e:
            logging.error("purge_user_tokens :: %r", e, exc_info=True)
            await db.rollback()
            raise HTTPException(status_code=TokenDB.SERVER_ERROR.value.status,
                                detail={"code": TokenDB.SERVER_ERROR.value.code,
                                        "message": TokenDB.SERVER_ERROR.value.message})
    
    @staticmethod
    async def update_token(db: AsyncSession, payload: dict, email: str) -> bool:
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
                                            .values(email=email,
                                                    issued_at=issued_at,
                                                    expires_at=expires_at,
                                                    revoked=False)
                                            .execution_options(synchronize_session="fetch"))
        try:
            result = await db.execute(query)
            await db.flush()
            return bool(result.rowcount)
        except SQLAlchemyError:
            await db.rollback()
            raise HTTPException(status_code=TokenDB.SERVER_ERROR.value.status,
                                detail={"code": TokenDB.SERVER_ERROR.value.code,
                                        "message": TokenDB.SERVER_ERROR.value.message})
        
    @staticmethod
    async def insert_token(db: AsyncSession, payload: dict, email: str) -> None:
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
        query = insert(RefreshToken).values(email=email, 
                                                jti=payload["jti"],
                                                issued_at=issued_at,
                                                expires_at=expires_at,
                                                revoked=False)
        try:
            await db.execute(query)
            await db.flush()
        except SQLAlchemyError:
            await db.rollback()
            raise HTTPException(status_code=TokenDB.SERVER_ERROR.value.status,
                                detail={"code": TokenDB.SERVER_ERROR.value.code,
                                        "message": TokenDB.SERVER_ERROR.value.message})
        

class TotalScoreDB:
    @staticmethod
    async def register_user(db: AsyncSession, record: TotalScore) -> None:
        db.add(record)
        await db.flush()         # SQL 전송 + PK 할당
        await db.refresh(record)
        # 예외처리 안씀 ? 예외처리 작성 완료시 해당 주석 삭제할 것

    @staticmethod
    async def delete_user(db: AsyncSession, name: str) -> None:
        query = delete(TotalScore).where(TotalScore.user_name == name)
        try:
            await db.execute(query)
            await db.flush()
        except SQLAlchemyError:
            await db.rollback()
            raise HTTPException(status_code=TokenDB.SERVER_ERROR.value.status,
                                detail={"code": TokenDB.SERVER_ERROR.value.code,
                                        "message": TokenDB.SERVER_ERROR.value.message})