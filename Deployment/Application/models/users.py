from sqlalchemy import Column, String, Integer, DateTime, Boolean, func

from Application.models.db import Base


# MySQL DB 의 Users 테이블에 대한 ORM 객체
class User(Base):
    __tablename__ = "Users"

    id = Column(Integer, primary_key= True, autoincrement= True)
    email = Column(String(32), unique= True, nullable= False) # 로그인용 email (unique)
    user_name = Column(String(16), unique= True, nullable= False) # 사용자 이름(닉네임)
    user_pw = Column(String(64), nullable= False) # 해시된 password 저장
    created_at = Column(DateTime, nullable= False, server_default= func.now())        
    updated_at = Column(DateTime, nullable= True, onupdate= func.now())
    status = Column(String(6), nullable= False, default= "active", comment= "계정 상태(active, banned)")