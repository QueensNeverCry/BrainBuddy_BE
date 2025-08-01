from pydantic import BaseModel
from pydantic import Field, model_validator, field_validator
from typing import Type, Dict, Any
import re

from app.api.auth.exceptions import SignUp, Login, Withdraw

NamePattern = r'^[A-Za-z0-9가-힣_-]{2,16}$'

# 회원가입 Request.body
class SignUpRequest(BaseModel):
    email: str = Field(...)
    user_name: str = Field(...)
    user_pw: str = Field(...)
    user_pw_confirm: str = Field(...)
    
    # Endpoint 도달 전, pydantic 모델로 검증 : 모든 field 값 존재 확인
    @model_validator(mode="before")
    @classmethod
    def check_fields(cls: Type["SignUpRequest"], values: Dict[str, Any]) -> Dict[str, Any]:
        required_fields = ["user_name", "email", "user_pw", "user_pw_confirm"]
        missing = [f for f in required_fields if f not in values or values[f] in (None, '')]
        if missing: # 필수값이 하나라도 누락시, app 로 에러 반환
            raise SignUp.INVALID_FORMAT.exc()
        return values
    
    # Endpoint 도달 전, pydantic 모델로 검증 : name, id, pw 길이 검사 (name 은 정규표현식으로 형식 검사까지)
    @field_validator("user_name")
    @classmethod
    def check_name_length(cls: Type["SignUpRequest"], name: str) -> str:
        if not (2 <= len(name) <= 16):
            raise SignUp.INVALID_FORMAT.exc()
        if not re.match(NamePattern, name):
            raise SignUp.INVALID_FORMAT.exc()
        return name
    
    @field_validator("email")
    @classmethod
    def check_id_length(cls: Type["SignUpRequest"], email: str) -> str:
        if not (5 <= len(email) <= 32):
            raise SignUp.INVALID_FORMAT.exc()
        return email
    
    @field_validator("user_pw")
    @classmethod
    def check_pw_length(cls: Type["SignUpRequest"], pw: str) -> str:
        if not (8 <= len(pw) <= 24):
            raise SignUp.INVALID_FORMAT.exc()
        return pw
    
    @field_validator("user_pw_confirm")
    @classmethod
    def check_pw_length(cls: Type["SignUpRequest"], pw_confirm: str) -> str:
        if not (8 <= len(pw_confirm) <= 24):
            raise SignUp.INVALID_FORMAT.exc()
        return pw_confirm
    
    # Endpoint 도달 전, pydantic 모델로 검증 : pw 와 pw_confirm 일치 확인
    @model_validator(mode="after")
    @classmethod
    def check_pw_match(cls: Type["SignUpRequest"], values: "SignUpRequest") -> "SignUpRequest":
        if values.user_pw != values.user_pw_confirm:
            raise SignUp.INVALID_PW.exc()
        return values

# 회원가입 성공 Response
class SignUpResponse(BaseModel):
    status: str = Field("success")
    user_name: str = Field(..., min_length=2)
    message: str = Field("Sign-Up Completed.")
    code: str = Field("CREATED")



# 로그인 Request
class LogInRequest(BaseModel):
    email: str = Field(...)
    user_pw: str = Field(...)

    # Endpoint 도달 전, pydantic 모델로 검증 : 모든 field 값 존재 확인
    @model_validator(mode="before")
    @classmethod
    def check_all_fields_exist(cls: Type["LogInRequest"], values: Dict[str, Any]) -> Dict[str, Any]:
        required_fields = ["email", "user_pw"]
        missing = [f for f in required_fields if f not in values or values[f] in (None, '')]
        if missing:
            raise Login.WRONG_FORMAT.exc()
        return values
    # Endpoint 도달 전, pydantic 모델로 검증 : id, pw 길이 검사
    @field_validator("email")
    @classmethod
    def check_id_length(cls: Type["LogInRequest"], id: str) -> str:
        if not (5 <= len(id) <= 32):
            raise Login.WRONG_FORMAT.exc()
        return id
    
    @field_validator("user_pw")
    @classmethod
    def check_pw_length(cls: Type["LogInRequest"], pw: str) -> str:
        if not (8 <= len(pw) <= 24):
            raise Login.WRONG_FORMAT.exc()
        return pw
    
# 로그인 성공 Response
class LogInResponse(BaseModel):
    status: str = Field("success")
    user_name: str = Field(...)
    message: str = Field("Login Completed.")
    code: str = Field("LOGIN_SUCCESS")



# 토큰 갱신 Response
class RenewResponse(BaseModel):
    status: str = Field("success")
    message: str = Field("Token refreshed successfully.")
    code: str = Field("REFRESHED")



# 로그아웃 Response
class LogOutResponse(BaseModel):
    status: str = Field("success")
    message: str = Field("You have been logged out successfully.")
    code: str = Field("LOGOUT")



# 회원 탈퇴 Request.body
class WithdrawRequest(BaseModel):
    email: str = Field(...)
    user_pw: str = Field(...)

    # Endpoint 도달 전, pydantic 모델로 검증 : 모든 field 값 존재 확인
    @model_validator(mode="before")
    @classmethod
    def check_fields(cls: Type["WithdrawRequest"], values: Dict[str, Any]) -> Dict[str, Any]:
        required_fields = ["email", "user_pw"]
        missing = [f for f in required_fields if f not in values or values[f] in (None, '')]
        if missing:
            raise Withdraw.INVALID_FORMAT.exc()
        return values
    # email 형식 확인
    @field_validator("email")
    @classmethod
    def check_id_length(cls: Type["WithdrawRequest"], id: str) -> str:
        if not (5 <= len(id) <= 32):
            raise Withdraw.INVALID_FORMAT.exc()
        return id
    # user_pw 형식 확인
    @field_validator("user_pw")
    @classmethod
    def check_pw_length(cls: Type["WithdrawRequest"], pw: str) -> str:
        if not (8 <= len(pw) <= 24):
            raise Withdraw.INVALID_FORMAT.exc()
        return pw

# 회원 탈퇴 Response.body
class WithdrawResponse(BaseModel):
    status: str = Field("success")
    message: str = Field("Account successfully withdrawn.")
    code: str = Field("WITHDRAW")