from pydantic import BaseModel
from pydantic import Field, model_validator, field_validator

from typing import Type, Dict, List, Any
from datetime import datetime, timezone
import re

from Application.api.dashboard.exceptions import Report

NamePattern = r'^[A-Za-z0-9가-힣_-]{2,16}$'

# ranking 객체의 요소
class UserRankingItem(BaseModel):
    rank: int
    score: int
    user_name: str
    total_cnt: int
    avg_focus: float
    trend: bool

# history 객체의 요소
class UserHistoryItem(BaseModel):
    date: str         # 학습 일자 (예: "2025-01-08")
    score: int        # 점수
    subject: str      # 과목
    time: str         # 시작 시간 (예: "15:30:00") -> ("오후 HH:MM")
    duration: int     # 학습 시간 (123)
    place: str        # 학습 장소 ("학교")
    avg_focus: float
    min_focus: int
    max_focus: int

# 직전 완료한 학습에 대한 레포트
class UserRecentReport(BaseModel):
    score: int
    duration: str
    avg_focus: float
    max_focus: int
    min_focus: int
    message: str

# 주간 ranking 응답 body
class RankingResponse(BaseModel):
    total_users: int
    ranking: List[UserRankingItem]

# 사용자 main page 응답 body
class MainResponse(BaseModel):
    status: str
    user_name: str
    total_users: int
    avg_focus: float
    current_rank: str
    total_study_cnt: int
    history: List[UserHistoryItem]

# 사용자 학습 완료 직후 분석레포트    
class RecentResponse(BaseModel):
    status: str = Field(...) # success | skipped
    report: UserRecentReport | None