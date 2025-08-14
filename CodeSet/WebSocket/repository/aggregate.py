from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date, time
from dataclasses import dataclass, asdict

from WebSocket.orm import TotalScore, StudySession, User

@dataclass
class DailyRecord:
    user_name:  str          # 학습자 ID
    started_at: datetime     # 학습 시작 시각 (UTC 권장)
    study_time: int          # 학습 시간(초 단위, duration seconds)
    subject:    str          # 학습 과목(Subject)
    location:   str          # 학습 장소(Location)
    score:      int          # 학습 점수(Score)
    avg_focus:  float        # 평균 집중도
    min_focus:  int          # 최소 집중도
    max_focus:  int          # 최대 집중도

class ScoreDB:
    @staticmethod
    async def increase_total_cnt(db: AsyncSession, user_name: str) -> None:
        query = (update(TotalScore).where(TotalScore.user_name == user_name)
                                        .values(total_cnt=TotalScore.total_cnt + 1)
                                        .execution_options(synchronize_session="fetch"))
        await db.execute(query)

class StudyDB:
    @staticmethod
    async def insert_daily(db: AsyncSession, record: DailyRecord) -> None:
        # dataclass → dict → ORM 인스턴스
        data = asdict(record)
        orm_obj = StudySession(**data)
        db.add(orm_obj)

