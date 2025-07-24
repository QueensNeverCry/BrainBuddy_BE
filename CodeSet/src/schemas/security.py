from pydantic import BaseModel, Field

# 로그아웃 API response.body
# 프론트에서 별도의 body 없이 쿠키/헤더로 토큰을 전송하기 때문에 Request 없음
class LogOutResponse(BaseModel):
    status: str = Field(..., example="success")
    message: str = Field(..., example="로그아웃 되었습니다.")