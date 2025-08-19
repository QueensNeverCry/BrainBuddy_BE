from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from Application.core.deps import AsyncDB, GetCurrentUser
from Application.core.exceptions import Server

from Application.api.dashboard.service import RankingService, MainService
from Application.api.dashboard.schemas import RankingResponse, MainResponse, RecentResponse



router = APIRouter()



# --- 주간 사용자 순위 제공 API [HTTP GET : http://{ServerDNS}/api/dashboard/weekly-ranking] ------------
@router.get(path="/weekly-ranking",
            status_code=status.HTTP_200_OK,
            summary="Weekly User Ranking",
            description="Provides the weekly ranking of users based on their scores over the past 7 days.")
async def get_weekly_ranking(db: AsyncSession = Depends(AsyncDB.get_db)) -> RankingResponse:
    try:
        await RankingService.renew_total_score(db=db)
        ranking = await RankingService.get_ranking_list(db=db)
        total = await RankingService.get_total_cnt(db=db)
        return RankingResponse(total_users=total, ranking=ranking)
    except SQLAlchemyError:
        raise Server.DB_ERROR.exc()
# --------------------------------------------------------------------------------------------------


# --- 사용자의 main page 구성 데이터 요청 API [HTTPS GET : https://{ServerDNS}/api/dashboard/main-info] ---
@router.get(path="/main-info",
            summary="Get Main Page User Info",
            description="Provides the key data for configuring the user's main page.")
async def get_main_info(user_name: str = Depends(GetCurrentUser),
                        db: AsyncSession = Depends(AsyncDB.get_db)) -> MainResponse:
    try:
        params = await MainService.get_main_params(db, user_name)
        return MainResponse(status="success",
                            user_name=user_name,
                            total_users=params["total_users"],
                            avg_focus=params["avg_focus"],
                            current_rank=params["rank"],
                            total_study_cnt=params["total_study_cnt"],
                            # COMPONENT_CNT 보다 적은 개수인 경우, None 을 대체한 경우에 대해 공유할 것 !!!
                            history=await MainService.get_history(db, user_name))
    except SQLAlchemyError:
        raise Server.DB_ERROR.exc()
# ---------------------------------------------------------------------------------------------------


# --- 사용자의 학습 종료 직후 리포트 요청 API [HTTPS GET : https://{ServerDNS}/api/dashboard/recent-report/me] ---
@router.get(path="/recent-report/me",
            summary="Recent Learning Analytics Request",
            description="Return the analysis result data immediately after the user's study session ends.")
async def get_study_report(name: str = Depends(GetCurrentUser),
                           db: AsyncSession = Depends(AsyncDB.get_db)) -> RecentResponse:
    try:
        print(f"{name}")
        res: dict = await MainService.fetch_recent_study(db, name)
    except SQLAlchemyError:
        raise Server.DB_ERROR.exc()
    return RecentResponse(status="success" if res else "skipped",
                          final_score=res.get("final_score"),
                          duration=res.get("duration"),
                          avg_focus=res.get("avg_focus"),
                          max_focus=res.get("max_focus"),
                          min_focus=res.get("min_focus"),
                          final_grade=res.get("final_grade"),
                          final_ment=res.get("final_ment"))
# --------------------------------------------------------------------------------------------------------