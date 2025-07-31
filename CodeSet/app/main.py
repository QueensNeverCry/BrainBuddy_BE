from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.users import router as users_router

from app.api.auth.utils import get_code_info

app = FastAPI()
app.include_router(auth_router, prefix="/api/auth")
app.include_router(users_router, prefix="/api/users")

# pydantic 의 모델 단 에서 먼저 Error 처리
@app.exception_handler(RequestValidationError)
async def auth_validation_handler(request: Request, 
                                  exc: RequestValidationError):
    # 에러 code에 따라 SignUpCode Enum에서 정보를 추출
    print(exc.errors()) 
    for error in exc.errors():
        # 1) Pydantic이 보관한 원래 예외(ValueError) 꺼내기
        ctx_error = error.get("ctx", {}).get("error")
        if isinstance(ctx_error, ValueError):
            code_str = str(ctx_error)      
        else:
            # 2) fallback: msg 에서 콤마 다음 부분만 추출
            raw = error.get("msg", "")
            code_str = raw.split(",", 1)[-1].strip()
        code_info = get_code_info(code_str)
        if code_info:
            return JSONResponse(status_code=code_info.status,
                                content={"status": "fail",
                                         "code": code_info.code, 
                                         "message": code_info.message})
    # 기타 예외
    return JSONResponse(status_code=status.HTTP_418_IM_A_TEAPOT,
                        content={"status": "fail",
                                 "code": "INVALID_REQ",
                                 "message": str(object=exc.errors())})

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