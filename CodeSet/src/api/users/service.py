from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import time, datetime, timezone
from typing import List

from src.core.config import COMPONENT_CNT
from src.models.score import TotalScore, UserDailyScore

from src.api.users.repository import Users, Scores 
from src.api.users.schemas import UserRankingItem, UserHistoryItem


def parse_minutes(t: time) -> int:
    return (t.hour * 60 + t.minute)

def parse_time(t: time) -> str:
    period = "오전" if t.hour < 12 else "오후"
    hour = t.hour % 12
    if hour == 0:
        hour = 12
    minute = f"{t.minute:02d}"
    return f"{period} {hour}:{minute}"

class RankingService:
    # 전체 active 사용자 수 반환
    @staticmethod
    async def get_total_cnt(db: AsyncSession) -> int:
        return await Users.get_active_cnt(db)

    # 주간 랭킹 리스트 List 반환
    async def get_ranking_list(db: AsyncSession) -> List[UserRankingItem]:
        return await Scores.sort_total_score(db)


class MainService:
    async def fetch_name(users_db: AsyncSession, email: str) -> str:
        return await Users.get_name(users_db, email)
    
    # fetch main params
    async def get_main_params(db: AsyncSession, name: str) -> dict:
        result = {}
        record = await Scores.get_TotalScore_record(db, name)
        rank = await Scores.get_user_rank(db, name)
        result["total_users"] = await Users.get_active_cnt(db)
        result["avg_focus"] = record.avg_score
        result["total_study_cnt"] = record.total_cnt
        result["rank"] = "-" if not rank else str(rank)
        return result

    # 사용자에 대한 COMPONENT_CNT 개수의 과거 학습 분석 기록 리스트 반환
    async def get_history(db: AsyncSession, name: str) -> List[UserHistoryItem]:
        records : List[UserDailyScore] = await Scores.get_recent_records(db, name, COMPONENT_CNT)
        result = [UserHistoryItem(date=str(record.score_date) if record is not None else "",
                                  score=record.score if record is not None else 0,
                                  subject=record.subject if record is not None else "",
                                  time=parse_time(record.start_time) if record is not None else "",
                                  duration=parse_minutes(record.study_time) if record is not None else 0,
                                  place=record.location if record is not None else "") 
                                  for record in records]
        return result