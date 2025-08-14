from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from asyncio import TimeoutError
from typing import Dict

from WebSocket.core.deps import AsyncDB, Get
from WebSocket.core.exceptions import TokenVerdict
from WebSocket.service import TokenService, RealTimeService, ModelService, FocusTracker

from WebSocket.ws.manager import ConnectionManager

router = APIRouter()
manager = ConnectionManager()
focus_tracker = FocusTracker()

# HandShake 최초 호출
@router.websocket("/real-time") # 프론트에서 query string 끝에 user_name, subject, location 입력해야함 !!
async def websocket_endpoint(websocket: WebSocket,
                             db: AsyncSession = Depends(AsyncDB.get_db),
                             params: Dict = Depends(Get.Parameters)) -> None:
    verdict = await TokenService.verify_tokens(db=db, access=params["access"], 
                                              refresh=params["refresh"], 
                                              user_name=params["user_name"])
    # HandShake 수락
    await websocket.accept()
    if verdict != TokenVerdict.VALID:
        await websocket.close(code=verdict.code, reason=verdict.reason)
        return
    # ConnectionManager 등록 (user_name : websocket)
    user_name = params['user_name']
    print(f"[CONNECTED] : {user_name}")
    manager.connect(user_name, websocket)
    focus_tracker.init_user(user_name)
    try:
        while True:
            try:
                # 1. 프레임 수집
                file_name = await RealTimeService.collect_frames(websocket, user_name)
                # 2. 추론
                # cur_focus = ModelService.inference_focus(file_name)
                cur_focus = await ModelService.test_inference(file_name)
                # 3. focus 갱신 / 집계
                result = await focus_tracker.update_focus(user_name, cur_focus)
                # 4. result 를 client 에게 송신
                await manager.send_current_focus(user_name, result)
            except TimeoutError:
                print(f"[LOG] : {user_name} disconnected by time-out.")
                await websocket.close(code=1000, reason="Timeout")
                break
            except WebSocketDisconnect:
                print(f"[LOG] : {user_name} Client disconnected.")
                break
    finally:
        manager.disconnect(user_name)
        print(f"[LOG] : {user_name} Disconnected.")
    score = await focus_tracker.compute_score(db, 
                                              user_name, 
                                              params["location"], 
                                              params["subject"])
    # await focus_tracker.update_total(db, user_name, score)
    

    #       - 컬럼을 확장 ? 아니면 단순히 study 기록을 분리...? (정규화 vs 비정규화)
    # 2. 유저가 연결하자마자 바로 끊은 경우 : compute_score에서 내부적으로 “데이터 유무 체크” & “예외처리/skip” 구현  -> 최소 5분 초과만 학습 점수 연산 및 기록
    # 3. handler 의 while True 문단 좀 더럽다...
    # 4. 현재 웹소켓 서버  layer achitecture 좀더 생각해보기
    # 5. Nginx 만들어야지...
    # 6. 현재 WAS / WS 서버의 DB 는 전부 동일 인스턴스를 기준으로 되어있음. 이 또한 변경할 것...