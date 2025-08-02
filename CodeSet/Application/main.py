from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from Application.api.auth import router as auth_router
from Application.api.dashboard import router as dashboard_router


app = FastAPI()

app.add_middleware(CORSMiddleware,
                   allow_origins=["http://localhost:5173"],
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"])

app.include_router(auth_router, prefix="/api/auth")
app.include_router(dashboard_router, prefix="/api/dashboard")

@app.exception_handler(HTTPException)
async def custom_error_handler(request: Request, exc: HTTPException):
    status_code = exc.status_code
    detail = exc.detail
    # detail에서 code/message 사용
    if isinstance(detail, dict):
        code = detail.get("code", "INTERNAL_SERVER_ERROR")
        message = detail.get("message", "WHY MESSAGE FIELD IS EMPTY ?")
    else:
        code = "INTERNAL_SERVER_ERROR"
        message = str(detail)
    # 응답    
    return JSONResponse(status_code=status_code,
                        content={"status": "fail",
                                 "code": code,
                                 "message": message})