from sqlalchemy import func, select, exists, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from Application.models.users import User
from Application.models.score import TotalScore, UserDailyScore
from Application.core.config import STUDY_TIME_THRESHOLD

from Application.api.dashboard.schemas import UserRankingItem, UserRecentReport

# Users 테이블
class UsersDB:
    # "status" 컬럼이 "active"인 유저 수 집계
    @staticmethod
    async def get_active_cnt(db: AsyncSession) -> int:
        query = select(func.count()).where(User.status == "active")
        result = await db.execute(query)
        return result.scalar_one()
    
    @staticmethod
    async def exists_user_name(db: AsyncSession, user_name: str) -> bool:
        query = select(exists().where(User.user_name == user_name))
        result = await db.execute(query)
        return result.scalar()


class ScoreDB:
    #
    @staticmethod
    async def sort_total_score(db: AsyncSession) -> List[UserRankingItem]:
        query = (select(TotalScore.user_name,
                        TotalScore.total_score,
                        TotalScore.avg_score.label("avg_focus"),
                        TotalScore.total_cnt).order_by(desc(TotalScore.total_score)))
        result = await db.execute(query)
        rows = result.all()  # List[Tuple[str, int, float, int]]
        rank_list: List[UserRankingItem] = []
        for rank, (name, total_score, avg_focus, total_cnt, trend) in enumerate(rows, start=1): # trend 로직 써야함 
            rank_list.append(UserRankingItem(rank=rank,
                                             score=total_score,
                                             user_name=name,
                                             total_cnt=total_cnt,
                                             avg_focus= avg_focus,
                                             trend= trend))
        return rank_list
    
    @staticmethod
    async def get_TotalScore_record(db: AsyncSession, name: str) -> TotalScore | None:
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
    async def get_prev_records(db: AsyncSession, name: str, cnt: int) -> List[UserDailyScore | None]:
        query = (select(UserDailyScore).where(UserDailyScore.user_name == name)
                                            .order_by(desc(UserDailyScore.started_at))
                                            .limit(cnt))
        result = await db.execute(query)
        records = result.scalars().all()
        if len(records) < cnt:
            records += [None] * (cnt - len(records))
        return records
    
    @staticmethod
    async def get_recent_record(db: AsyncSession, name: str) -> UserDailyScore | None:
        # study_time이 5분(300초) 이하인 경우는 제외 (웹소켓 서버에서도 동일하게 300초 이하 인 경우 학습으로 간주하지 않음 (DB 접근 overhead 최소화))
        query = (select(UserDailyScore)
                    .where(UserDailyScore.user_name == name, UserDailyScore.study_time > STUDY_TIME_THRESHOLD)
                    .order_by(desc(UserDailyScore.started_at))
                    .limit(1))
        rows = await db.execute(query)
        return rows.scalars().first()
        
        