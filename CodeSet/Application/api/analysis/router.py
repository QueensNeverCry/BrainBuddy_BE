from fastapi import APIRouter, Request, Response, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from Application.core.deps import AsyncDB, GetCurrentUser
from Application.core.exceptions import Server





router = APIRouter()

# @router.get("/recent-result",
#              status_code=status.HTTP_200_OK,
#              summary="compute recent study score",
#              description="사용자의 완료한 직전 학습의 결과 데이터 가져오기")