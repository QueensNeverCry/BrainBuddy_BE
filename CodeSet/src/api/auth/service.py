# src/services/auth_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.models.users import User
import bcrypt
import uuid
from jose import jwt, JWTError
from datetime import datetime, timezone, timedelta
from src.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_SEC

# 주어진 id 를 사용하는 사용자가 DB에 있는지 조회
def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.user_id == user_id).first()

# 회원가입한 사용자 DB 등록
def create_user(db: Session, user_id: str, user_name: str, password: str) -> User | None:
    if get_user_by_id(db, user_id):
        return None  # 이미 존재하는 id
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(user_id= user_id, user_name= user_name, password= hashed)
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail= f"회원가입 처리 중 서버 에러: {e}")
    return user

# 로그인 시도 한 사용자의 인증
def authenticate_user(db: Session, user_id: str, password: str) -> User | None:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return None
    if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        return None
    return user

# 첫 JWT 토큰 생성
def create_access_token(data: dict) -> str:
    secret_key = JWT_SECRET_KEY
    algorithm = JWT_ALGORITHM
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds= ACCESS_TOKEN_EXPIRE_SEC)
    to_encode.update( { "exp": expire,
                        "jti": str(uuid.uuid4()),
                        "user_id": data["user_id"] } )
    try:
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm= algorithm)
        return encoded_jwt
    except JWTError as e:
        raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"JWT 토큰 생성 실패: {e}")