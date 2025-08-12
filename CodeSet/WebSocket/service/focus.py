from typing import Dict
from collections import deque
from datetime import datetime, timezone, time, timedelta
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession

from WebSocket.repository import ScoreDB, StudyDB, DailyRecord

@dataclass
class FocusInfo:
    bits: deque = field(default_factory=lambda: deque(maxlen=10))
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime = field(default_factory=datetime.now)
    score: int = 0
    avg_focus: float = 0
    min_focus: int = 10
    max_focus: int = 0
    duration: int = 0

class FocusTracker:
    def __init__(self) -> None:
        self.focus_dict: Dict[str, FocusInfo] = {}
    
    # 사용자 집중도 dict 초기화
    def init_user(self, user_name: str) -> None:
        self.focus_dict[user_name] = FocusInfo()
        print(f"        {self.focus_dict[user_name].start_time}")

    # 사용자 실시간 집중도 최신화
    def update_focus(self, user_name: str, focus: int) -> int:
        self.focus_dict[user_name].bits.append('1' if focus == 1 else '0')
        current = sum(1 for b in self.focus_dict[user_name].bits if b == '1')
        self.focus_dict[user_name].score += current
        self.focus_dict[user_name].min_focus = min(current, self.focus_dict[user_name].min_focus)
        self.focus_dict[user_name].max_focus = max(current, self.focus_dict[user_name].max_focus)
        self.focus_dict[user_name].duration += 1
        self.focus_dict[user_name].avg_focus = self.focus_dict[user_name].score / self.focus_dict[user_name].duration
        return current

    # 사용자 학습 종료
    def end_session(self, user_name: str) -> None:
        now = datetime.now(timezone.utc)
        self.focus_dict[user_name].end_time = now

    # 학습 구간의 집중도 연산 및 DB - UserDaily에 기록
    async def compute_score(self, db: AsyncSession, user_name: str, location: str, subject: str) -> int:
        # 최근 학습 종합 집중도 계산
        bits, start, end, score, avg, mn, mx, duration = self.focus_dict[user_name]
        self.focus_dict.pop(user_name)
        # score_date, start_time, study_time 계산
        duration = end - start
        if duration > timedelta(minutes=0):
            score_date = start.date()  # Date
            start_time = start.time()  # Time HH:MM:SS
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
                                 score=score,
                                 avg_focus= avg,
                                 min_focus= mn,
                                 max_focus= mx)
            # StudyDB 에 기록
            async with db.begin():
                await StudyDB.insert_daily(db, record)
            return score
        else:
            return -1