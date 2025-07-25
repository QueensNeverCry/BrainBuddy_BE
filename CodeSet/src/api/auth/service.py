# src/services/auth_service.py
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
import bcrypt
import uuid
from jose import jwt, JWTError
from datetime import datetime, timezone, timedelta

from src.models.users import User
from src.models.security import RefreshToken
from src.core.security import get_payload, is_token_blacklisted
from src.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_SEC, REFRESH_TOKEN_EXPIRE_SEC

REQUIRED_CLAIMS = ["exp", "jti", "user_id"]

# 주어진 id 를 사용하는 사용자가 DB에 있는지 조회
def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.user_id == user_id).first()

# 주어진 id 에 해당하는 사용자를 table에서 제거
def erase_user_by_id(db: Session, user_id: str) -> int:
    deleted = db.query(User).filter(User.user_id == user_id).delete()
    try:
        db.commit()
    except:
        db.rollback()
    return deleted 

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
    
# 로그인한 사용자, Refreshed 사용자의 Refresh 토큰 DB 에 저장
def add_refresh_token(db: Session, refresh_token: str, user_id: str) -> None:
    try:
        # 만료(expired) 또는 폐기(revoked) 토큰 먼저 삭제
        db.query(RefreshToken)\
            .filter( RefreshToken.user_id == user_id,
                    (RefreshToken.expires_at <= datetime.now(timezone.utc)) | 
                    (RefreshToken.revoked == True) )\
            .delete(synchronize_session=False)
        # 새 토큰 정보 추출
        refresh_payload = get_payload(refresh_token)
        expires_at = datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc)
        # 만료 안된 토큰이 있으면 update
        updated = db.query(RefreshToken)\
                    .filter( RefreshToken.user_id == user_id,
                             RefreshToken.revoked == False, 
                             RefreshToken.expires_at > datetime.now(timezone.utc) )\
                    .update({ "refresh_token": refresh_token,
                                     "issued_at": datetime.now(timezone.utc),
                                     "expires_at": expires_at,
                                     "revoked": False })
        # 만료 안된 토큰이 없다면 insert (신규 추가)
        if updated == 0:
            new_token = RefreshToken( refresh_token=refresh_token,
                                      user_id=user_id,
                                      issued_at=datetime.now(timezone.utc),
                                      expires_at=expires_at,
                                      revoked=False )
            db.add(new_token)
        # 트랜잭션 전체 한번에 commit
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Refresh Token 처리 중 서버 에러: {e}")
# 사용자의 Refresh 토큰 유효성 검사
def check_refresh_token(db: Session, refresh: str) -> dict:
    try:
        payload = jwt.decode(refresh, JWT_SECRET_KEY, JWT_ALGORITHM)
        if is_token_blacklisted(payload["jti"]): # 블랙리스트 검증
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="이 토큰은 더 이상 사용할 수 없습니다 (블랙리스트 처리됨).")
        missing = [k for k in REQUIRED_CLAIMS if k not in payload]
        if missing: # claim 검증
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="토큰에 필수 claim이 없습니다.")
        token_row = db.query(RefreshToken)\
                        .filter( RefreshToken.refresh_token == refresh,
                                 RefreshToken.revoked == False,
                                 RefreshToken.expires_at > datetime.now(timezone.utc) ).first()
        if not token_row:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="유효한 Refresh Token이 아닙니다.")
    except jwt.ExpiredSignatureError: # 만료 검증
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="만료된 refresh 토큰 입니다.")
    except jwt.JWTError: # 서명 검증, decoding 오류
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="유효하지 않은 토큰입니다.")
    return payload

# 사용자의 Refresh 토큰 table 에서 제거
def erase_refresh_token(db: Session, refresh: str) -> None:
    try:
        db.query(RefreshToken).filter(RefreshToken.refresh_token == refresh).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail= f"Refresh Token 처리 중 서버 에러: {e}")