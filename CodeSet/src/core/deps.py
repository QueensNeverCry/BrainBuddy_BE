from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from src.core.security import get_payload
from src.models.users import User

from sqlalchemy.orm import Session
from src.core.database import UsersSession

def get_users_db():
    db: Session = UsersSession()
    try:
        yield db  # 세션을 호출 함수에 넘김
    finally:
        db.close()  # 작업 끝나면 세션 닫기(메모리/커넥션 누수 방지)


# ACCESS 토큰 발급 API 경로 지정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/log-in")

# ACCESS 토큰에 대해서만 아래 함수 실행, 
def get_user(db= Depends(get_users_db), token: str = Depends(oauth2_scheme)) -> User | None:
    payload = get_payload(token)
    user = db.query(User).filter(User.user_id == payload["user_id"]).first()
    if user is None:
        raise HTTPException(status_code=401, detail="유효하지 않은 인증")
    return user
