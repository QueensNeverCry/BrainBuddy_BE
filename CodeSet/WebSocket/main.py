from fastapi import FastAPI
from contextlib import asynccontextmanager

from WebSocket.ws import handler as ws_handler
from WebSocket.service import ModelService

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Startup] 모델 로딩 중...")
    ModelService.load_model()
    print("[Startup] 모델 로드 완료")
    yield
    print("[Shutdown] 서버 종료")

app = FastAPI()

app.include_router(ws_handler, "/ws")