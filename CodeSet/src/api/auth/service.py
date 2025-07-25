# src/services/auth_service.py
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
import bcrypt
import uuid
from jose import jwt, JWTError
from datetime import datetime, timezone, timedelta

from src.models.users import User
from src.models.security import RefreshToken
from src.core.deps import get_refresh_tokens_db
from src.core.security import get_payload
from src.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_SEC, REFRESH_TOKEN_EXPIRE_SEC

# 주어진 id 를 사용하는 사용자가 DB에 있는지 조회
def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.user_id == user_id).first()

# 회원가입한 사용자 DB 등록
def add_user(db: Session, user_id: str, user_name: str, password: str) -> User | None:
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

# JWT ACCESS 토큰 생성
def create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds= ACCESS_TOKEN_EXPIRE_SEC)
    payload.update( { "exp": expire,
                      "jti": str(uuid.uuid4()),
                      "user_id": data["user_id"] } )
    try:
        access_token = jwt.encode(payload, key= JWT_SECRET_KEY, algorithm= JWT_ALGORITHM)
        return access_token
    except JWTError as e:
        raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail= f"[FAIL] - JWT ACCESS TOKEN : {e}")

# Refresh 토큰 생성
def create_refresh_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds= REFRESH_TOKEN_EXPIRE_SEC)
    payload.update( { "exp": expire,
                      "jti": str(uuid.uuid4()),
                      "user_id": data["user_id"] } )
    try:
        refresh_token = jwt.encode(payload, key= JWT_SECRET_KEY, algorithm= JWT_ALGORITHM)
        return refresh_token
    except JWTError as e:
        raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail= f"[FAIL] - JWT REFRESH TOKEN : {e}")
    
# 로그인한 사용자의 Refresh 토큰 DB 에 저장
def add_refresh_token(db: Session, refresh_token: str, user_id: str, device_id: str) -> None:
    # refresh_token의 exp 추출
    refresh_payload = get_payload(refresh_token)
    expires_at = datetime.fromtimestamp(refresh_payload["exp"], tz= timezone.utc)
    # 이전의 Refresh 토큰 무효화
    db.query(RefreshToken)\
      .filter(RefreshToken.user_id == user_id, 
              RefreshToken.revoked == False, 
              RefreshToken.expires_at > datetime.now(timezone.utc))\
      .update({"revoked": True})
    # 새로운 refresh_token을 테이블에 등록
    new_token = RefreshToken( refresh_token= refresh_token,
                              user_id= user_id,
                              device_id= device_id,
                              issued_at= datetime.now(timezone.utc),
                              expires_at= expires_at,
                              revoked= False )
    try:
        db.add(new_token)
        db.commit()
        db.refresh(new_token)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail= f"Refresh Token 처리 중 서버 에러: {e}")