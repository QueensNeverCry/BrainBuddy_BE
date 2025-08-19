from sqlalchemy.ext.asyncio import AsyncSession
from datetime import time, datetime
from typing import List

from Application.core.config import COMPONENT_CNT
from Application.models.score import StudySession

from Application.api.dashboard.repository import UsersDB, ScoreDB, StudyDB
from Application.api.dashboard.schemas import UserRankingItem, UserHistoryItem, UserRecentReport



def parse_time(t: datetime) -> str:
    period = "오전" if t.hour < 12 else "오후"
    hour = t.hour % 12
    if hour == 0:
        hour = 12
    minute = f"{t.minute:02d}"
    return f"{period} {hour}:{minute}"

def parse_minutes(seconds: int) -> int:
    return seconds // 60

def change_format(seconds: int) -> str:
    hour = seconds // 3600
    minute = (seconds % 3600) // 60
    return f"{hour}:{minute}"

def parse_grade(avg_focus: float) -> str:
    if avg_focus >= 7.5 :
        return "A"
    elif avg_focus >= 5.0 :
        return "B"
    elif avg_focus >= 2.5 :
        return "C"
    return "D"

def parse_ment(avg_focus: float) -> str:
    if avg_focus >= 7.5 :
        return "놀라운 집중력이예요! 계속 이 패턴을 유지하세요!"
    elif avg_focus >= 5.0 :
        return "훌륭한 집중력입니다! 조금만 더 노력하면 완벽해요!"
    elif avg_focus >= 2.5 :
        return "괜찮은 시작이예요! 환경을 개선하면 더 좋아질 거예요!"
    return "다음에는 더 잘할 수 있어요! 포기하지 마세요!"


class RankingService:
    # 전체 active 사용자 수 반환
    # READ-ONLY process
    @staticmethod
    async def get_total_cnt(db: AsyncSession) -> int:
        async with db.begin():
            return await UsersDB.get_active_cnt(db)

    # 주간 랭킹 리스트 List 반환
    # WRITE process
    @staticmethod
    async def get_ranking_list(db: AsyncSession) -> List[UserRankingItem]:
        async with db.begin():
            return await ScoreDB.sort_total_score(db)

    # 주간 기록 최신화
    # WRITE process
    async def renew_total_score(db: AsyncSession) -> None:
        async with db.begin():
            ranking = await StudyDB.renew_records(db)
            await ScoreDB.renew_table(db, ranking)

class MainService:    
    # fetch main params
    # READ-ONLY process
    @staticmethod
    async def get_main_params(db: AsyncSession, name: str) -> dict:
        result = {}
        async with db.begin():
            record = await ScoreDB.get_TotalScore_record(db, name)
            rank = await ScoreDB.get_user_rank(db, name)
            result["total_users"] = await UsersDB.get_active_cnt(db)
        result["avg_focus"] = record.avg_focus if record else 0
        result["total_study_cnt"] = record.total_cnt if record else 0
        result["rank"] = str(rank) if rank else "-"
        return result

    # 사용자에 대한 COMPONENT_CNT 개수의 과거 학습 분석 기록 리스트 반환
    # READ-ONLY process
    async def get_history(db: AsyncSession, name: str) -> List[UserHistoryItem]:
        async with db.begin():
            records : List[StudySession | None] = await StudyDB.get_prev_records(db, name, COMPONENT_CNT)
        result = [UserHistoryItem(date=str(record.started_at.date()) if record else "",
                                  score=record.score if record else 0,
                                  subject=record.subject if record else "",
                                  time=parse_time(record.started_at) if record else "",
                                  duration=parse_minutes(record.study_time) if record else 0,
                                  place=record.location if record else "",
                                  avg_focus=record.avg_focus if record else 0.0,
                                  min_focus=record.min_focus if record else 0,
                                  max_focus=record.max_focus if record else 0)
                                  
                                  for record in records]
        return result

    # 사용자의 직전에 완료한 학습 결과 데이터 반환
    # READ-ONLY process
    async def fetch_recent_study(db: AsyncSession, name: str) -> dict | None:
        async with db.begin():
            row : StudySession | None = await StudyDB.get_recent_record(db, name)
        if row:
            return {"final_score": row.score,
                    "duration": change_format(row.study_time),
                    "avg_focus": row.avg_focus,
                    "max_focus": row.max_focus,
                    "min_focus": row.min_focus,
                    "final_grade": parse_grade(row.avg_focus),
                    "final_ment": parse_ment(row.avg_focus)}
        else:
            return None