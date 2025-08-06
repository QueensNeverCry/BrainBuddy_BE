from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date, time
from dataclasses import dataclass, asdict

from WebSocket.models import TotalScore, UserDailyScore

@dataclass
class DailyRecord:
    user_name:  str      # 학습자 ID
    score_date: date     # 학습 일 (Date)
    start_time: time     # 학습 시작 시각 (Time)
    study_time: time     # 학습 시간 (Time, duration as HH:MM:SS)
    subject:    str      # 학습 과목 (Subject)
    location:   str      # 학습 장소 (Location)
    score:      float    # 학습 점수 (Score)

class TotalScoreTable:
    @staticmethod
    async def func_1():
        x = 10

class UserDailyTable:
    @staticmethod
    async def insert_daily(db: AsyncSession, record: DailyRecord):
        # dataclass → dict → ORM 인스턴스
        data = asdict(record)
        orm_obj = UserDailyScore(**data)
        db.add(orm_obj)

