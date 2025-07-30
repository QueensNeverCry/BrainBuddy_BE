from sqlalchemy import func, select, update, delete, insert, exists, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from datetime import datetime, timezone
from typing import List

from src.models.users import User
from src.models.score import TotalScore, UserDailyScore

from src.api.users.response_code import ScoreDB
from src.api.users.schemas import UserRankingItem, UserHistoryItem

# Users 테이블
class Users:
    @staticmethod
    async def get_name(db: AsyncSession, email: str) -> str:
        query = select(User.user_name).where(User.email == email)
        result = await db.execute(query)
        name = result.scalar_one_or_none()
        return name

    # "status" 컬럼이 "active"인 유저 수 집계
    @staticmethod 
    async def get_active_cnt(db: AsyncSession) -> int:
        query = select(func.count()).where(User.status == "active")
        result = await db.execute(query)
        return result.scalar_one()


class Scores:
    @staticmethod
    async def sort_total_score(db: AsyncSession) -> List[UserRankingItem]:
        query = select(TotalScore.user_name, TotalScore.total_score).order_by(desc(TotalScore.total_score))
        result = await db.execute(query)
        rows = result.all()
        rank_list = []
        for rank, (name, total_score) in enumerate(rows, start=1):  # 랭킹 1부터
            rank_list.append(UserRankingItem(rank=rank, score=total_score, user_name=name))
        return rank_list
    
    @staticmethod
    async def get_TotalScore_record(db: AsyncSession, name: str) -> TotalScore:
        query = select(TotalScore).where(TotalScore.user_name==name)
        result = await db.execute(query)
        record = result.one_or_none()
        return record

    @staticmethod
    async def get_user_rank(db: AsyncSession, name: str) -> int | None:
        # 먼저 해당 유저의 total_score를 구함
        score_query = select(TotalScore.total_score).where(TotalScore.user_name == name)
        user_score_result = await db.execute(score_query)
        user_score = user_score_result.scalar_one_or_none()
        if user_score is None or user_score is 0.0:
            return None
        # user_score보다 큰 점수 가진 사람의 수 + 1 = 랭킹
        rank_query = select(func.count()).where(TotalScore.total_score > user_score)
        rank_result = await db.execute(rank_query)
        higher_cnt = rank_result.scalar_one()
        return higher_cnt + 1
    
    @staticmethod
    async def get_recent_records(db: AsyncSession, name: str, cnt: int) -> List[UserDailyScore | None]:
        query = (select(UserDailyScore).where(UserDailyScore.user_name == name)
                                            .order_by(UserDailyScore.created_at.desc())
                                            .limit(cnt))
        result = await db.execute(query)
        records = result.scalars().all()
        if len(records) < cnt:
            records += [None] * (cnt - len(records))
        return records

    # @staticmethod
    # async def get_user_total_cnt(db: AsyncSession, email: str) -> int:
    #     query = select(TotalScore).where(TotalScore.email==email)
    #     result = await db.execute(query)
    #     rows = result.all()
    #     return len(rows)
    
    # @staticmethod
    # async def get_user_avg(db: AsyncSession, email: str) -> float | None:
    #     query = select(TotalScore.avg_score).where(TotalScore.email==email)
    #     result = await db.execute(query)
    #     value = result.scalar_one_or_none()
    #     return value
    
