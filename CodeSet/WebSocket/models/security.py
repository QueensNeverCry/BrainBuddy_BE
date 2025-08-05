from sqlalchemy import Column, String, Integer, DateTime, Boolean, func

from WebSocket.models.db import Base


# 장기 인증 상태의 안전한 관리를 위해 RefreshToken 은 서버 내 DB table을 이용하여 관리 -> RTR 방식
class RefreshToken(Base):
    __tablename__ = "RefreshTokens" 
    
    id = Column(Integer, primary_key= True, autoincrement= True)
    jti = Column(String(36), nullable= False, unique= True)
    user_name = Column(String(16), nullable= False)
    issued_at = Column(DateTime, nullable= False, default= func.now())
    expires_at = Column(DateTime, nullable= False)
    revoked = Column(Boolean, default= False)
    # device_id = Column(String(30), nullable= False)