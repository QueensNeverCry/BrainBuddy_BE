from fastapi import APIRouter, Request, Response, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from Application.core.deps import AsyncDB, GetCurrentUser
from Application.core.exceptions import Server

from Application.api.dashboard.service import UserService, RankingService, MainService
from Application.api.dashboard.schemas import RankingResponse, MainResponse, StudyPlanRequest, StudyPlanResponse


router = APIRouter()



# 주간 사용자 순위 제공 API [HTTP GET : http://{ServerDNS}/api/dashboard/weekly-ranking]
@router.get(path="/weekly-ranking",
            status_code=status.HTTP_200_OK,
            summary="Weekly User Ranking",
            description="Provides the weekly ranking of users based on their scores over the past 7 days.")
async def get_weekly_ranking(db: AsyncSession = Depends(AsyncDB.get_db)) -> RankingResponse:
    try:
        await db.begin()
        total = await RankingService.get_total_cnt(db)
        ranking = await RankingService.get_ranking_list(db)
        return RankingResponse(total_users=total, ranking=ranking)
    except SQLAlchemyError:
        await db.rollback()
        raise Server.DB_ERROR.exc()



# 사용자의 main page 구성 데이터 요청 API [HTTPS GET : https://{ServerDNS}/api/dashboard/main-info]
@router.get(path="/main-info",
            summary="Get Main Page User Info",
            description="Provides the key data for configuring the user's main page.")
async def get_main_info(email: str = Depends(GetCurrentUser),
                        db: AsyncSession = Depends(AsyncDB.get_db)) -> MainResponse:
    await db.begin()
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



# 학습을 시작한 사용자의 학습 메타 데이터 기록 API [HTTPS POST : https://{ServerDNS}/api/dashboard/study-plan]
@router.post(path="/study-plan",
             summary="Create study plan",
             description="Write current study's meta-data.")
async def create_study_plan(payload: StudyPlanRequest,
                            email: str = Depends(GetCurrentUser),
                            db: AsyncSession = Depends(AsyncDB.get_db),) -> StudyPlanResponse:
    try:
        await db.begin()
        name = await UserService.parse_name(db, email)
        await MainService.create_plan(db, name, payload.when, payload.where, payload.what)
        await db.commit()
        return StudyPlanResponse(status="success", start_time=payload.when)
    except SQLAlchemyError:
        await db.rollback()
        raise Server.DB_ERROR.exc()
    # except Exception as e:
    #     await db.rollback()
    #     logging.error(f"Error in create_study_plan: {str(e)}")
    #     traceback.print_exc()
    #     raise HTTPException(status_code=status.HTTP_418_IM_A_TEAPOT,
    #                         detail={"code": "DEBUG",
    #                                 "message": "Need to branch error handling : study-plan api."})