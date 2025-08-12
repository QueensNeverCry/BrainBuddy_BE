from sqlalchemy import select, update, delete, insert, exists, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
import logging

from Application.models.users import User
from Application.models.score import TotalScore, StudySession
from Application.models.security import RefreshToken



class UsersDB:
    @staticmethod
    async def check_name(db: AsyncSession, name: str) -> bool:
        query = select(exists().where(User.user_name == name))
        result = await db.execute(query)
        return bool(result.scalar())
    
    @staticmethod
    async def check_email(db: AsyncSession, email: str) -> bool:
        query = select(exists().where(User.email == email))
        result = await db.execute(query)
        return bool(result.scalar())
    
    @staticmethod
    async def exist_user(db: AsyncSession, email: str, user_name: str) -> bool:
        query = select(exists().where((User.email == email) | (User.user_name == user_name)))
        result = await db.execute(query)
        return bool(result.scalar())
    
    @staticmethod
    async def get_user(db: AsyncSession, email: str) -> User | None:
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        return user
    
    @staticmethod
    async def is_valid_user(db: AsyncSession, user_name: str) -> bool:
        cond = and_(User.user_name == user_name, User.status == "active")
        query = select(exists().where(cond))
        res = await db.execute(query)
        return bool(res.scalar_one())
    
    @staticmethod
    async def get_email_by_name(db: AsyncSession, name: str) -> str | None:
        query = select(User.email).where(User.user_name == name)
        result = await db.execute(query)
        email = result.scalar_one_or_none()
        return email

    @staticmethod
    async def register_user(db: AsyncSession, user: User) -> None:
        db.add(user)
    
    @staticmethod
    async def is_active_user(db: AsyncSession, name: str) -> bool:
        query = select(User.status).where(User.user_name == name)
        status = await db.scalar(query)  # 없으면 None 반환
        return status == "active"
    
    @staticmethod
    async def delete_user(db: AsyncSession, email: str) -> None:
        query = delete(User).where(User.email == email)
        try:
            await db.execute(query)
        except SQLAlchemyError:
            raise



class RefreshDB:
    @staticmethod
    async def purge_user_tokens(db: AsyncSession, name: str) -> None:
        now = datetime.now(timezone.utc)
        # DELETE 쿼리: user_name 일치 + (expires_at <= now OR revoked = True)
        query = (delete(RefreshToken).where(RefreshToken.user_name == name,  
                                                ((RefreshToken.expires_at <= now) | (RefreshToken.revoked == True)))
                                           .execution_options(synchronize_session="fetch") )
        try:
            await db.execute(query)
        except SQLAlchemyError:
            raise

    @staticmethod
    async def insert_token(db: AsyncSession, payload: dict, name: str) -> None:
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
        query = insert(RefreshToken).values(user_name=name, 
                                                jti=payload["jti"],
                                                issued_at=issued_at,
                                                expires_at=expires_at,
                                                revoked=False)
        try:
            await db.execute(query)
        except SQLAlchemyError:
            raise
    
    @staticmethod
    async def update_token(db: AsyncSession, payload: dict, name: str) -> bool:
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
                                            .values(user_name=name,
                                                    issued_at=issued_at,
                                                    expires_at=expires_at,
                                                    revoked=False)
                                            .execution_options(synchronize_session="fetch"))
        try:
            result = await db.execute(query)
            await db.flush()
            return bool(result.rowcount)
        except SQLAlchemyError:
            raise
        


class TotalScoreDB:
    @staticmethod
    async def register_user(db: AsyncSession, record: TotalScore) -> None:
        db.add(record)

    @staticmethod
    async def delete_user(db: AsyncSession, name: str) -> None:
        query = delete(TotalScore).where(TotalScore.user_name == name)
        try:
            await db.execute(query)
        except SQLAlchemyError:
            raise



class StudyDB:
    @staticmethod
    async def delete_records(db: AsyncSession, name: str) -> None:
        query = delete(table=StudySession).where(StudySession.user_name == name)
        try:
            await db.execute(query)
        except SQLAlchemyError:
            raise