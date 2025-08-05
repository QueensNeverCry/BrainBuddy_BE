from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from asyncio import TimeoutError
from WebSocket.core.deps import AsyncDB, Get
from WebSocket.service import TokenService, RealTimeService, CloseCodes

from WebSocket.ws.manager import ConnectionManager

router = APIRouter()
manager = ConnectionManager()

# HandShake 직후 최초 호출
@router.websocket("/real-time")
async def websocket_endpoint(websocket: WebSocket,
                             db: AsyncSession = Depends(AsyncDB.get_db),
                             access: str = Depends(Get.AccessToken),
                             refresh: str = Depends(Get.RefreshToken),
                             user_name: str = Depends(Get.UserName)):
    verdict = await TokenService.verify_tokens(db=db, access=access, refresh=refresh, user_name=user_name)
    # HandShake 수락
    await websocket.accept()
    if verdict != "valid":
        await websocket.send_json(CloseCodes[verdict])
        await websocket.close(code=CloseCodes[verdict]["code"])
        return
    # ConnectionManager 등록 (user_name : websocket)
    manager.connect(user_name, websocket)
    try:
        while True:
            try:
                await manager.send_personal_message(user_name, "Hello")
                file_name = await RealTimeService.collect_frames(websocket, user_name)
            except TimeoutError:
                print(f"[LOG] : {user_name} Disconnected by 30s time-out.")
                await websocket.close(code=1000, reason="Timeout")
                break
            except WebSocketDisconnect:
                print(f"[LOG] : {user_name} Disconnected from Client.")
                break
    finally:
        manager.disconnect(user_name)
        print(f"[LOG] : {user_name} Disconnected.")