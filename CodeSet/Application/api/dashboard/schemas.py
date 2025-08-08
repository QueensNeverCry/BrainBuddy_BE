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
    score: float
    user_name: str
    total_cnt: int
    avg_focus: float
    trend: bool

# history 객체의 요소
class UserHistoryItem(BaseModel):
    date: str         # 학습 일자 (예: "2025-01-08")
    score: float      # 점수
    subject: str      # 과목
    time: str         # 시작 시간 (예: "15:30:00") -> ("오후 HH:MM")
    duration: int     # 학습 시간 (123)
    place: str        # 학습 장소 ("학교")
#   report_id: int    # 리포트 ID (보류)

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
class ReportRequest(BaseModel):
    user_name: str = Field(...)

    @model_validator(mode="before")
    @classmethod
    def check_field(cls: Type["ReportRequest"], values: Dict[str, Any]) -> Dict[str, Any]:
        required_field = "user_name"
        # required_field 가 없으면 verdict 에 삽입, required_field 가 아닌 field 가 있으면 verdict 에 삽입
        if required_field not in values:
            raise Report.FORBIDDEN.exc()
        for field in values.keys():
            if field != required_field:
                raise Report.FORBIDDEN.exc()
        return values
    
    @field_validator("user_name")
    @classmethod
    def check_name_length(cls: Type["ReportRequest"], name: str) -> str:
        if not (2 <= len(name) <= 16):
            raise Report.FORBIDDEN.exc()
        if not re.match(NamePattern, name):
            raise Report.FORBIDDEN.exc()
        return name
    
class ReportResponse(BaseModel):
    status: str = Field("success")
    avg_focus: float
    min_focus: float
    max_focus: float
    duration: str # time.strftime