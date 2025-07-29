from fastapi import APIRouter, HTTPException, Request, Response, Depends, status
from sqlalchemy.orm import Session

# 공통으로 사용하는 핵심 로직 or 필수 컴포넌트
from src.core.deps import get_users_db
from src.core.security import get_payload, parse_token, blacklist_token
from src.core.config import ACCESS, REFRESH, ACCESS_TOKEN_EXPIRE_SEC, REFRESH_TOKEN_EXPIRE_SEC
from src.schemas.security import LogOutResponse
from src.models.users import User

# auth domain 이내의 component import
from src.api.auth.schemas import ( SignUpRequest, SignUpResponse,
                                   LogInRequest, LogInResponse,
                                   RenewResponse,
                                   WithdrawRequest, WithdrawResponse )