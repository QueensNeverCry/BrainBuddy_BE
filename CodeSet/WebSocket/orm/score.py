from sqlalchemy import Column, ForeignKey, UniqueConstraint, String, Integer, Double, DateTime, Boolean, func

from WebSocket.orm.db import Base


# 사용자의 학습 score 관리
class TotalScore(Base):
    __tablename__ = "TotalScore"

    id = Column(Integer, primary_key=True, autoincrement= True)
    user_name = Column(String(16), ForeignKey("Users.user_name"), unique=True, nullable=False)
    total_score = Column(Integer, nullable=False, default=0) # 사용자의 기간 내 종합 점수
    avg_focus = Column(Double, nullable=False, default=0.0) # 사용자의 기간 내 평균 집중도
    total_cnt = Column(Integer, nullable=False, default=0) # 사용자의 전체 기간 동안 학습한 횟수
    prev_rank = Column(Integer, nullable=False, default=0) # 갱신 이전의 순위

# 사용자의 학습 일, 학습 시간, 학습 과목, 학습 장소 단위 score 기록
class StudySession(Base):
    __tablename__ = "StudySession"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(16), ForeignKey("Users.user_name"), nullable=False)
    started_at = Column(DateTime, nullable=False)   # 학습 시작 시각 (2025-08-09 14:25:00)
    study_time = Column(Integer, nullable=True)      # 학습 시간(초 단위)
    subject = Column(String(32), nullable=False)   # 학습 과목(Subject)
    location = Column(String(32), nullable=False)  # 학습 장소(Location)
    score = Column(Integer, nullable=False, default=0) # 학습 점수
    avg_focus = Column(Double, nullable=False, default=0.0)
    min_focus = Column(Integer, nullable=False, default=0)
    max_focus = Column(Integer, nullable=False, default=0)

    # 한 유저가 같은 일, 동일 시간, 과목, 장소에 여러 점수를 기록하지 않도록 Unique 제약
    __table_args__ = (
        UniqueConstraint('user_name', 'started_at', name='uix_user_start_detail'),
    )