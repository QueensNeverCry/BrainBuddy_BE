from fastapi import FastAPI
from src.core.preemptive_middleware import PreemptiveTokenRefreshMiddleware

app = FastAPI()

# 미들웨어 등록
app.add_middleware(PreemptiveTokenRefreshMiddleware)

# 아래에 API 라우터 등록 등...