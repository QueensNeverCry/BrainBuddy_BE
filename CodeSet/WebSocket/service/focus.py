from typing import Dict
from bitarray import bitarray
from datetime import datetime, timezone, time
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from repository import TotalScoreTable, UserDailyTable, DailyRecord

@dataclass
class FocusInfo:
    bits: bitarray
    start_time: datetime
    end_time: datetime

class FocusTracker:
    def __init__(self) -> None:
        # user_name -> bitarray
        self.focus_dict: Dict[str, FocusInfo] = {}
    
    # 사용자 집중도 dict 초기화
    def init_user(self, user_name: str) -> None:
        now = datetime.now(timezone.utc)
        self.focus_dict[user_name] = FocusInfo(bits=bitarray(), start_time=now, end_time=now)

    # 사용자 집중도 최신화
    def append_focus(self, user_name: str, focus: int) -> None:
        self.focus_dict[user_name].bits.append(focus)

    # 사용자 학습 종료
    def end_session(self, user_name: str) -> None:
        now = datetime.now(timezone.utc)
        self.focus_dict[user_name].end_time = now

    # 학습 구간의 집중도 연산 및 DB - UserDaily에 기록
    async def compute_score(self, db: AsyncSession, user_name: str, location: str, subject: str) -> None:
        # 최근 학습 종합 집중도 계산
        bits, start, end = self.focus_dict[user_name]
        self.focus_dict.pop(user_name)
        # 종합 집중도 계산 ~ 구현해라
        score = 10
        # ~ 종합 집중도 계산
        # score_date, start_time, study_time 계산
        score_date = start.date()                  # Date
        start_time = start.time()                  # Time HH:MM:SS
        duration = end - start                     # timedelta
        hours, rem = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        study_time = time(hour=hours, minute=minutes, second=seconds)
        # DailyScoreRecord 객체 생성
        record = DailyRecord(user_name=user_name,
                             score_date=score_date,
                             start_time=start_time,
                             study_time=study_time,
                             subject=subject,
                             location=location,
                             score=score)
        # UserDailyTable 에 기록
        async with db.begin():
            await UserDailyTable.insert_daily(db, record)