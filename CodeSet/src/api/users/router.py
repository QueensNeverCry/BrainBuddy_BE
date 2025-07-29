from fastapi import APIRouter, Request, Response, HTTPException, Depends, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.deps import AsyncDB, GetCurrentUser

from src.api.users.service import RankingService, MainService
from src.api.users.schemas import RankingResponse, MainResponse

router = APIRouter()



# 주간 사용자 순위 제공 API [HTTP GET : http://{ServerDNS}/api/users/weekly-ranking]
@router.get(path="/users/weekly-ranking",
            status_code=status.HTTP_200_OK,
            summary="Weekly User Ranking",
            description="Provides the weekly ranking of users based on their scores over the past 7 days.")
async def get_weekly_ranking(response: RankingResponse,
                             users_db: AsyncSession = Depends(AsyncDB.get_users),
                             score_db: AsyncSession = Depends(AsyncDB.get_score_tables)) -> RankingResponse:
    RankingResponse.total_users = await RankingService.get_total_cnt(users_db)
    RankingResponse.ranking = await RankingService.get_ranking_list(users_db, score_db)
    return RankingResponse



# 사용자의 main page 구성 데이터 요청 API [HTTPS GET : https://{ServerDNS}/api/users/main-info]
@router.get(path="/users/main-info",
            status=status.HTTP_200_OK,
            summary="Get Main Page User Info",
            description="Provides the key data for configuring the user's main page.")
async def get_main_info(email: str = Depends(GetCurrentUser),
                        users_db: AsyncSession = Depends(AsyncDB.get_score_tables),
                        score_db: AsyncSession = Depends(AsyncDB.get_score_tables)) -> MainResponse:
    params = await MainService.get_main_params(users_db, score_db, email)
    return MainResponse(status="success",
                        user_name=MainService.fetch_name(users_db, email),
                        total_users=params["total_users"],
                        avg_focus=params["avg_focus"],
                        current_rank=params["rank"],
                        total_study_cnt=params["total_study_cnt"],
                        # COMPONENT_CNT 보다 적은 개수인 경우, None 을 대체한 경우에 대해 공유할 것 !!!
                        history=await MainService.get_history(score_db, email))
