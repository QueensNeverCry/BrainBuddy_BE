# src/models/users.py
from sqlalchemy import Column, String, Integer, DateTime, Boolean, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "Users"

    id = Column(Integer, primary_key= True, autoincrement= True)
    user_id = Column(String(30), unique= True, nullable= False)      # 로그인용 ID (unique)
    user_name = Column(String(30), nullable= False)                  # 사용자 이름(닉네임)
    password = Column(String(128), nullable= False)                  # 해시된 password 저장
    tutorial_skip = Column(Boolean, nullable= False, default= False) # 튜토리얼 스킵 여부
    created_at = Column(DateTime, nullable= False, server_default= func.now())        
    updated_at = Column(DateTime, nullable= True, onupdate= func.now())
    status = Column(String(6), nullable= False, default= "active", comment= "계정 상태(active, banned)")

    def __repr__(self):
        return f"<User(id={self.id}, user_id='{self.user_id}', user_name='{self.user_name}')>"
