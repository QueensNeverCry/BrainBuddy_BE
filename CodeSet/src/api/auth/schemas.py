# src/api/auth/schemas.py
from pydantic import BaseModel, Field

# 회원가입 API request.body
class SignUpRequest(BaseModel):
    user_name: str = Field(..., min_length= 2)
    user_id: str = Field(...)
    password: str = Field(..., min_length= 8)
# 회원가입 API response.body
class SignUpResponse(BaseModel):
    status: str = Field(...)
    user_name: str = Field(..., min_length= 2)
    user_id: str = Field(...)

# 로그인 API request.body
class LogInRequest(BaseModel):
    user_id: str = Field(...)
    password: str = Field(..., min_length= 8)
    device_id: str = Field(...) # 프론트 단에서 device_id 추출 후, body에 담아줘야 함 !!
# 로그인 API response.body
class LogInResponse(BaseModel):
    status: str = Field(...)
    user_name: str = Field(..., min_length= 2)
    user_id: str = Field(...)

# JWT access 토큰 재발급 response.body
class RenewResponse(BaseModel):
    status: str = Field(...)

# 회원탈퇴 API request.body
class WithdrawRequest(BaseModel):
    user_id: str = Field(...)
    password: str = Field(...)

# 회원탈퇴 API response.body
class WithdrawResponse(BaseModel):
    status: str = Field(...)
    message: str = Field(...)