from sqlalchemy.ext.asyncio import AsyncSession
from datetime import time, datetime
from typing import List

from Application.core.config import COMPONENT_CNT
from Application.models.score import TotalScore, UserDailyScore

from Application.api.dashboard.repository import UsersDB, ScoresDB, DailyDB
from Application.api.dashboard.schemas import UserRankingItem, UserHistoryItem


def parse_minutes(t: time) -> int:
    return (t.hour * 60 + t.minute)

def parse_time(t: time) -> str:
    period = "오전" if t.hour < 12 else "오후"
    hour = t.hour % 12
    if hour == 0:
        hour = 12
    minute = f"{t.minute:02d}"
    return f"{period} {hour}:{minute}"

class UserService:
    @staticmethod
    async def check_user_by_name(db: AsyncSession, user_name: str) -> bool:
        return await UsersDB.exists_user_name(db, user_name)

class RankingService:
    # 전체 active 사용자 수 반환
    @staticmethod
    async def get_total_cnt(db: AsyncSession) -> int:
        return await UsersDB.get_active_cnt(db)

    # 주간 랭킹 리스트 List 반환
    async def get_ranking_list(db: AsyncSession) -> List[UserRankingItem]:
        return await ScoresDB.sort_total_score(db)


class MainService:    
    # fetch main params
    @staticmethod
    async def get_main_params(db: AsyncSession, name: str) -> dict:
        result = {}
        record = await ScoresDB.get_TotalScore_record(db, name)
        rank = await ScoresDB.get_user_rank(db, name)
        result["total_users"] = await UsersDB.get_active_cnt(db)
        result["avg_focus"] = record.avg_score if record else 0
        result["total_study_cnt"] = record.total_cnt if record else 0
        result["rank"] = str(rank) if rank else "-"
        return result

    # 사용자에 대한 COMPONENT_CNT 개수의 과거 학습 분석 기록 리스트 반환
    async def get_history(db: AsyncSession, name: str) -> List[UserHistoryItem]:
        records : List[UserDailyScore] = await DailyDB.get_recent_records(db, name, COMPONENT_CNT)
        result = [UserHistoryItem(date=str(record.score_date) if record is not None else "",
                                  score=record.score if record is not None else 0,
                                  subject=record.subject if record is not None else "",
                                  time=parse_time(record.start_time) if record is not None else "",
                                  duration=parse_minutes(record.study_time) if record is not None else 0,
                                  place=record.location if record is not None else "") 
                                  for record in records]
        return result
