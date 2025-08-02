from sqlalchemy import func, select, update, delete, insert, exists, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import List

from Application.models.users import User
from Application.models.score import TotalScore, UserDailyScore

from Application.api.dashboard.schemas import UserRankingItem, UserHistoryItem

# Users 테이블
class UsersDB:
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


class ScoresDB:
    @staticmethod
    async def sort_total_score(db: AsyncSession) -> List[UserRankingItem]:
        query = (select(TotalScore.user_name,
                        TotalScore.total_score,
                        TotalScore.avg_score.label("avg_focus"),
                        TotalScore.total_cnt).order_by(desc(TotalScore.total_score)))
        result = await db.execute(query)
        rows = result.all()  # List[Tuple[str, float, float, int]]
        rank_list: List[UserRankingItem] = []

        for rank, (name, total_score, avg_focus, total_cnt) in enumerate(rows, start=1):
            rank_list.append(UserRankingItem(rank=rank, score=total_score, user_name=name, total_cnt=total_cnt, avg_focus= avg_focus))
        return rank_list
    
    @staticmethod
    async def get_TotalScore_record(db: AsyncSession, name: str) -> TotalScore:
        query = select(TotalScore).where(TotalScore.user_name==name)
        result = await db.execute(query)
        return result.scalars().one_or_none()

    @staticmethod
    async def get_user_rank(db: AsyncSession, name: str) -> int | None:
        # 먼저 해당 유저의 total_score를 구함
        score_query = select(TotalScore.total_score).where(TotalScore.user_name == name)
        user_score_result = await db.execute(score_query)
        user_score = user_score_result.scalar_one_or_none()
        if user_score is None or user_score == 0.0:
            return None
        # user_score보다 큰 점수 가진 사람의 수 + 1 = 랭킹
        rank_query = select(func.count()).where(TotalScore.total_score > user_score)
        rank_result = await db.execute(rank_query)
        higher_cnt = rank_result.scalar_one()
        return higher_cnt + 1


class DailyDB:    
    @staticmethod
    async def get_recent_records(db: AsyncSession, name: str, cnt: int) -> List[UserDailyScore | None]:
        query = (select(UserDailyScore).where(UserDailyScore.user_name == name)
                                .order_by(desc(UserDailyScore.score_date),desc(UserDailyScore.start_time))
                                .limit(cnt))
        result = await db.execute(query)
        records = result.scalars().all()
        if len(records) < cnt:
            records += [None] * (cnt - len(records))
        return records
    
    @staticmethod
    async def create_daily_record(db:AsyncSession, name: str, when: datetime, where: str, what: str) -> None:
        print(f"[DEBUG] :: (user name = {name})  (when = {when})  (where = {where})  (what = {what})")
        record = UserDailyScore(user_name=name,
                                score_date=when.date(),
                                start_time=when.time(),
                                study_time=None,
                                subject=what,
                                location=where)
        try:
            db.add(record)
            await db.flush()
            await db.refresh(record)
        except SQLAlchemyError:
            raise