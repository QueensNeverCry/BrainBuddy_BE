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
# 프론트에서 query string 끝에 user_name, subject, location 입력해야함 !!
@router.websocket("/real-time")
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
                img_dir = await RealTimeService.collect_frames(websocket, user_name)
                # 2. 추론
                cur_focus = await ModelService.inference_focus(img_dir)
                # 3. focus 갱신 / 집계
                result = await focus_tracker.update_focus(user_name, cur_focus)
                # 4. result 를 client 에게 송신
                await manager.send_current_focus(user_name, result)
                # 5. img_dir 삭제
                await RealTimeService.clear(img_dir)
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
    print(f"[LOG] : {user_name} 's score is {score}.")

    # 유저가 연결하자마자 바로 끊은 경우 : compute_score에서 내부적으로 “데이터 유무 체크” & “예외처리/skip” 구현  -> 최소 5분 초과만 학습 점수 연산 및 기록
    #   하지만, 실시간 시연시엔 5분 한도 해제...