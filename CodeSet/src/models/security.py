# src/models/security.py
from sqlalchemy import Column, String, Integer, DateTime, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
    
Base = declarative_base()

class RefreshToken(Base):
    __tablename__ = "RefreshTokens" 
    
    id = Column(Integer, primary_key= True)
    user_id = Column(String, nullable= False)
    refresh_token = Column(String, nullable= False, unique= True)
    issued_at = Column(DateTime, default= func.now())
    expires_at = Column(DateTime, nullable= False)
    revoked = Column(Boolean, default= False)