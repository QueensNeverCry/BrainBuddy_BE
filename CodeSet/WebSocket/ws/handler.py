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

# HandShake 직후 최초 호출
@router.websocket("/real-time") # 프론트에서 query string 끝에 user_name 입력해야함 !!
async def websocket_endpoint(websocket: WebSocket,
                             db: AsyncSession = Depends(AsyncDB.get_db),
                             params: Dict = Depends(Get.Parameters)):
    verdict = await TokenService.verify_tokens(db=db, access=params["access"], refresh=params["refresh"], user_name=params["name"])
    # HandShake 수락
    await websocket.accept()
    user_name = params["name"]
    if verdict != TokenVerdict.VALID:
        await websocket.close(code=verdict.code, reason=verdict.reason)
        return
    # ConnectionManager 등록 (user_name : websocket)
    manager.connect(user_name, websocket)
    focus_tracker.init_user(user_name)
    try:
        while True:
            try:
                # test 용 접속 메세지
                await manager.send_personal_message(user_name, "Hello")
                file_name = await RealTimeService.collect_frames(websocket, user_name)
                cur_focus = await ModelService.inference_focus(file_name)
                focus_tracker.append_focus(user_name, cur_focus)
            except TimeoutError:
                print(f"[LOG] : {user_name} Disconnected by 30s time-out.")
                focus_tracker.end_session(user_name)
                await websocket.close(code=1000, reason="Timeout")
                break
            except WebSocketDisconnect:
                focus_tracker.end_session(user_name)
                print(f"[LOG] : {user_name} Disconnected from Client.")
                break
    finally:
        manager.disconnect(user_name)
        print(f"[LOG] : {user_name} Disconnected.")
    # focus_tracker 가 보관중인 순간 집중도 데이터로 최근 학습 집중도 연산 -> DB 저장
    await focus_tracker.compute_score(db, 
                                      user_name, 
                                      params["location"], 
                                      params["subject"])
    
    # 근데, 실시간 현재 집중도 전송은 ??????????? 쒸발?????????
    # 유저가 연결하자마자 바로 끊은 경우 : compute_score에서 내부적으로 “데이터 유무 체크” & “예외처리/skip” 필요

    # 1. 최근 학습 기록 기반 학습 시간동안의 집중도 score 계산 구현
    # 2. 유저가 연결하자마자 바로 끊은 경우 : compute_score에서 내부적으로 “데이터 유무 체크” & “예외처리/skip” 구현
    # 3. handler 의 while True 문단 좀 더럽다...
    # 4. 현재 웹소켓 서버  layer achitecture 좀더 생각해보기
    # 5. Nginx 만들어야지...
    # 6. 현재 WAS / WS 서버의 DB 는 전부 동일 인스턴스를 기준으로 되어있음. 이 또한 변경할 것...