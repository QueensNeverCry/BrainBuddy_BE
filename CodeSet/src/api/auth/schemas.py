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
# 로그인 API response.body
class LogInResponse(BaseModel):
    status: str = Field(...)
    user_name: str = Field(..., min_length= 2)
    user_id: str = Field(...)

# JWT access 토큰 재발급 response.body
class TokenResponse(BaseModel):
    status: str = Field(...)