import asyncio
from typing import Dict, defaultdict
from collections import deque
from datetime import datetime, timezone
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession

from WebSocket.repository import ScoreDB, StudyDB, DailyRecord

@dataclass
class FocusInfo:
    bits: deque = field(default_factory=lambda: deque(maxlen=10))
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: datetime   = field(default_factory=lambda: datetime.now(timezone.utc))
    score: int = 0
    avg_focus: float = 0.0
    min_focus: int = 10
    max_focus: int = 0
    duration: int = 0

class FocusTracker:
    def __init__(self) -> None:
        self.focus_dict: Dict[str, FocusInfo] = {}
        self._locks = defaultdict(asyncio.Lock)
    
    def get_lock(self, user_name: str) -> asyncio.Lock:
        return self._locks[user_name]

    # 사용자 집중도 dict 초기화
    def init_user(self, user_name: str) -> None:
        self.focus_dict[user_name] = FocusInfo()
        print(f"        {self.focus_dict[user_name].start_time}")

    # 사용자 실시간 집중도 최신화
    async def update_focus(self, user_name: str, focus: int) -> int:
        self.focus_dict[user_name].bits.append('1' if focus == 1 else '0')
        print(f"[DEBUG] bits_len={len(self.focus_dict[user_name].bits)}, bits={list(self.focus_dict[user_name].bits)}, user={user_name!r}")
        current = sum(1 for b in self.focus_dict[user_name].bits if b == '1')
        self.focus_dict[user_name].score += current
        self.focus_dict[user_name].min_focus = min(current, self.focus_dict[user_name].min_focus)
        self.focus_dict[user_name].max_focus = max(current, self.focus_dict[user_name].max_focus)
        self.focus_dict[user_name].duration += 1
        self.focus_dict[user_name].avg_focus = self.focus_dict[user_name].score / self.focus_dict[user_name].duration
        print(f"[LOG] :     {user_name} current focus = {current}")
        return current

    # 학습 구간의 집중도 연산 및 DB - UserDaily에 기록
    async def compute_score(self, db: AsyncSession, user_name: str, location: str, subject: str) -> int:
        # 최근 학습 종합 집중도 계산
        info = self.focus_dict[user_name]  # type: FocusInfo
        start    = info.start_time
        end      = datetime.now(timezone.utc)
        score    = info.score
        avg      = info.avg_focus
        mn       = info.min_focus
        mx       = info.max_focus
        self.focus_dict.pop(user_name)
        # score_date, start_time, study_time 계산
        duration = int((end - start).total_seconds())
        if duration > 0:
            score_date = start.date()  # Date
            start_time = start.time()  # Time HH:MM:SS
            # DailyScoreRecord 객체 생성
            record = DailyRecord(user_name=user_name,
                                 started_at=start,
                                 study_time=duration,
                                 subject=subject,
                                 location=location,
                                 score=score,
                                 avg_focus= avg,
                                 min_focus= mn,
                                 max_focus= mx)
            # StudyDB 에 기록
            async with db.begin():
                await ScoreDB.increase_total_cnt(db, user_name)
                await StudyDB.insert_daily(db, record)
            return score
        else:
            return -1
