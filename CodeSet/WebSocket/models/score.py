from sqlalchemy import Column, ForeignKey, UniqueConstraint, String, Integer, Double, Date, Time, func
from datetime import datetime

from WebSocket.models.db import Base


# 사용자의 학습 score 관리
class TotalScore(Base):
    __tablename__ = "TotalScore"  

    id = Column(Integer, primary_key=True, autoincrement= True)
    user_name = Column(String(16), ForeignKey("Users.user_name"), unique=True, nullable=False)
    total_score = Column(Double, nullable=False, default=0.0) # 사용자의 기간 내 종합 점수
    avg_score = Column(Double, nullable=False, default=0.0) # 사용자의 기간 내 평균 점수
    total_cnt = Column(Integer, nullable=False, default=0) # 사용자의 전체 기간 동안 학습한 횟수

# 사용자의 학습 일, 학습 시간, 학습 과목, 학습 장소 단위 score 기록
class UserDailyScore(Base):
    __tablename__ = "UserDailyScore"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(16), ForeignKey("Users.user_name"), nullable=False)
    score_date = Column(Date, nullable=False)     # 학습 일(Date)
    start_time = Column(Time, nullable=False)     # 학습 시작 시각 (HH:MM:SS)
    study_time = Column(Time, nullable=True)      # 학습 시간(Time)
    subject = Column(String(32), nullable=False)   # 학습 과목(Subject)
    location = Column(String(32), nullable=False)  # 학습 장소(Location)
    score = Column(Double, nullable=False, default=0.0) # 학습 점수

    # 한 유저가 같은 일, 동일 시간, 과목, 장소에 여러 점수를 기록하지 않도록 Unique 제약
    __table_args__ = (
        UniqueConstraint('user_name', 'score_date', 'start_time', 'subject', 'location', name='uix_user_score_detail'),
    )