from fastapi import APIRouter, Request, Response, HTTPException, Depends, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.deps import AsyncDB, GetCurrentUser

from src.api.users.service import RankingService, MainService
from src.api.users.schemas import RankingResponse, MainResponse

router = APIRouter()



# 주간 사용자 순위 제공 API [HTTP GET : http://{ServerDNS}/api/users/weekly-ranking]
@router.get(path="/weekly-ranking",
            status_code=status.HTTP_200_OK,
            summary="Weekly User Ranking",
            description="Provides the weekly ranking of users based on their scores over the past 7 days.")
async def get_weekly_ranking(db: AsyncSession = Depends(AsyncDB.get_db)) -> RankingResponse:
    try:
        await db.begin()
        total = await RankingService.get_total_cnt(db)
        ranking = await RankingService.get_ranking_list(db)
        return RankingResponse(status="success", total_users=total, ranking=ranking)
    except:
        raise HTTPException(status_code=status.HTTP_418_IM_A_TEAPOT,
                            detail={"code": "DEBUG",
                                    "message": "Need to branch error handling."})



# 사용자의 main page 구성 데이터 요청 API [HTTPS GET : https://{ServerDNS}/api/users/main-info]
@router.get(path="/main-info",
            summary="Get Main Page User Info",
            description="Provides the key data for configuring the user's main page.")
async def get_main_info(email: str = Depends(GetCurrentUser),
                        db: AsyncSession = Depends(AsyncDB.get_db)) -> MainResponse:
    user_name = await MainService.fetch_name(db, email)
    params = await MainService.get_main_params(db, user_name)
    return MainResponse(status="success",
                        user_name=user_name,
                        total_users=params["total_users"],
                        avg_focus=params["avg_focus"],
                        current_rank=params["rank"],
                        total_study_cnt=params["total_study_cnt"],
                        # COMPONENT_CNT 보다 적은 개수인 경우, None 을 대체한 경우에 대해 공유할 것 !!!
                        history=await MainService.get_history(db, email))
