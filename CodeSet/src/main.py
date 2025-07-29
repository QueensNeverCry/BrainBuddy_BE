from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from src.api.auth import router as auth_router

app = FastAPI()
app.include_router(auth_router, prefix="/auth")

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    status_code = exc.status_code
    # detail에서 code/message 사용
    if isinstance(detail, dict):
        code = detail.get("code", "INTERNAL_SERVER_ERROR")
        message = detail.get("message", "")
    else:
        code = "INTERNAL_SERVER_ERROR"
        message = str(detail)
    # 응답    
    return JSONResponse(status_code=status_code,
                        content={"status": "fail",
                                 "code": code,
                                 "message": message})