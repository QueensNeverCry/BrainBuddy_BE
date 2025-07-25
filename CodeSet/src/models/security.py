# src/models/security.py
from sqlalchemy import Column, String, Integer, DateTime, Boolean, func
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


# 장기 인증 상태의 안전한 관리를 위해 RefreshToken 은 서버 내 DB table을 이용하여 관리
class RefreshToken(Base):
    __tablename__ = "RefreshTokens" 
    
    id = Column(Integer, primary_key= True, autoincrement= True)
    refresh_token = Column(String, nullable= False, unique= True)
    user_id = Column(String, nullable= False)
    device_id = Column(String, nullable= False)
    issued_at = Column(DateTime, nullable= False, default= func.now())
    expires_at = Column(DateTime, nullable= False)
    revoked = Column(Boolean, default= False)


# “로그아웃/강제 만료/관리자 일괄조치” 시 user_id 로 전체 토큰 회수
# 일정 기간(예: 30일, 90일, 6개월, 1년 등) 지난 만료+revoked 토큰은 배치/스케줄러로 삭제(CRUD 정리)