from pydantic import BaseModel, ValidationError
from pydantic import Field, model_validator, field_validator

from typing import Type, Dict, List
from datetime import datetime, timezone

# ranking 객체의 요소
class UserRankingItem(BaseModel):
    rank: int
    score: float
    user_name: str
    total_cnt: int
    avg_focus: float

# history 객체의 요소
class UserHistoryItem(BaseModel):
    date: str         # 학습 일자 (예: "2025-01-08")
    score: float      # 점수
    subject: str      # 과목
    time: str         # 시작 시간 (예: "15:30:00") -> ("오후 HH:MM")
    duration: int     # 학습 시간 (123)
    place: str        # 학습 장소 ("학교")
#    report_id: int    # 리포트 ID (보류)

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


# 학습 시작시, 사용자의 현재학습 메타데이터 기록 요청 body
class StudyPlanRequest(BaseModel):
    when: datetime
    where: str     = Field(...)
    what:  str     = Field(...)

    @model_validator(mode="before")
    @classmethod
    def forbid_and_inject_when(cls, values: dict) -> dict:
        # 1) 클라이언트가 when 을 보내면 에러
        if "when" in values: # Error 객체 커스텀 하면 바꿀것
            raise ValueError("`when` 필드는 클라이언트에서 지정할 수 없습니다.")
        # 2) 서버 현재 시간으로 주입
        values["when"] = datetime.now(timezone.utc)
        return values

# 학습 시작시, 사용자의 현재학습 메타데이터 기록 응답 body
class StudyPlanResponse(BaseModel):
    status: str
    start_time: datetime