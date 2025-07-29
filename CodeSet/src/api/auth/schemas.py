from pydantic import BaseModel, ValidationError
from pydantic import Field, model_validator, field_validator

from typing import Type, Dict, Any

from src.api.auth.response_code import SignUpCode, LogInCode, WithdrawCode



# 회원가입 Request.body를 pydantic 객체화
class SignUpRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=32)
    user_name: str = Field(..., min_length=2, max_length=16)
    user_pw: str = Field(...,min_length=8, max_length=16)
    user_pw_confirm: str = Field(...,min_length=8, max_length=16)
    
    # Endpoint 도달 전, pydantic 모델로 검증 : 모든 field 값 존재 확인
    @model_validator(mode="before")
    @classmethod
    def check_fields(cls: Type["SignUpRequest"], values: Dict[str, Any]) -> Dict[str, Any]:
        required_fields = ["user_name", "email", "user_pw", "user_pw_confirm"]
        missing = [f for f in required_fields if f not in values or values[f] in (None, '')]
        if missing: # 필수값이 하나라도 누락시, ValueError raise -> APIRouter 단위로 Error응답 커스텀 필요
            raise ValueError(SignUpCode.MISSING_REQ.value.code)
        return values
    
    # Endpoint 도달 전, pydantic 모델로 검증 : name, id, pw 길이 검사
    @field_validator("user_name")
    @classmethod
    def check_name_length(cls: Type["SignUpRequest"], name: str) -> str:
        if not (2 <= len(name) <= 16):
            raise ValueError(SignUpCode.INVALID_FORMAT.value.code)
        return name
    
    @field_validator("email")
    @classmethod
    def check_id_length(cls: Type["SignUpRequest"], email: str) -> str:
        if not (5 <= len(id) <= 32):
            raise ValueError(SignUpCode.INVALID_FORMAT.value.code)
        return email
    
    @field_validator("user_pw")
    @classmethod
    def check_pw_length(cls: Type["SignUpRequest"], pw: str) -> str:
        if not (8 <= len(pw) <= 16):
            raise ValueError(SignUpCode.INVALID_FORMAT.value.code)
        return pw
    
    @field_validator("user_pw_confirm")
    @classmethod
    def check_pw_length(cls: Type["SignUpRequest"], pw_confirm: str) -> str:
        if not (8 <= len(pw_confirm) <= 16):
            raise ValueError(SignUpCode.INVALID_FORMAT.value.code)
        return pw_confirm
    
    # Endpoint 도달 전, pydantic 모델로 검증 : pw 와 pw_confirm 일치 확인
    @model_validator(mode="after")
    @classmethod
    def check_pw_match(cls: Type["SignUpRequest"], values: SignUpCode) -> SignUpCode:
        if values.get("user_pw") != values.get("user_pw_confirm"):
            raise ValueError(SignUpCode.INVALID_PW.value.code)
        return values

# 회원가입 Response
class SignUpResponse(BaseModel):
    status: str = Field(...)
    user_name: str = Field(..., min_length=2)
    message: str = Field(...)
    code: str = Field(...)



# 로그인 Request
class LogInRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=32)
    user_pw: str = Field(...,min_length=8, max_length=16)

    # Endpoint 도달 전, pydantic 모델로 검증 : 모든 field 값 존재 확인
    @model_validator(mode="before")
    @classmethod
    def check_all_fields_exist(cls: Type["LogInRequest"], values: Dict[str, Any]) -> Dict[str, Any]:
        required_fields = ["email", "user_pw"]
        missing = [f for f in required_fields if f not in values or values[f] in (None, '')]
        if missing: # 필수값이 하나라도 누락시, ValueError raise -> APIRouter 단위로 Error응답 커스텀 필요
            raise ValueError(LogInCode.WRONG_FORMAT.value.code)
        return values
    # Endpoint 도달 전, pydantic 모델로 검증 : id, pw 길이 검사
    @field_validator("email")
    @classmethod
    def check_id_length(cls: Type["LogInRequest"], id: str) -> str:
        if not (5 <= len(id) <= 32):
            raise ValueError(LogInCode.WRONG_FORMAT.value.code)
        return id
    
    @field_validator("user_pw")
    @classmethod
    def check_pw_length(cls: Type["LogInRequest"], pw: str) -> str:
        if not (8 <= len(pw) <= 16):
            raise ValueError(LogInCode.WRONG_FORMAT.value.code)
        return pw
    
# 로그인 Response
class LogInResponse(BaseModel):
    status: str = Field(...)
    user_name: str = Field(..., min_length=2)
    message: str = Field(...)
    code: str = Field(...)



# 토큰 갱신 Response
class RenewResponse(BaseModel):
    status: str = Field(...)
    message: str = Field(...)
    code: str = Field(...)



# 로그아웃 Response
class LogOutResponse(BaseModel):
    status: str = Field(...)
    message: str = Field(...)
    code: str = Field(...)



# 회원 탈퇴 Request.body
class WithdrawReq(BaseModel):
    email: str = Field(..., min_length=5, max_length=32)
    user_pw: str = Field(...,min_length=8, max_length=16)

    # Endpoint 도달 전, pydantic 모델로 검증 : 모든 field 값 존재 확인
    @model_validator(mode="before")
    @classmethod
    def check_fields(cls: Type["WithdrawReq"], values: Dict[str, Any]) -> Dict[str, Any]:
        required_fields = ["email", "user_pw"]
        missing = [f for f in required_fields if f not in values or values[f] in (None, '')]
        if missing: # 필수값이 하나라도 누락시, ValueError raise -> APIRouter 단위로 Error응답 커스텀 필요
            raise ValueError(WithdrawCode.MISSING_REQ.value.code)
        return values
    # email 형식 확인
    @field_validator("email")
    @classmethod
    def check_id_length(cls: Type["WithdrawReq"], id: str) -> str:
        if not (5 <= len(id) <= 32):
            raise ValueError(WithdrawCode.INVALID_FORMAT.value.code)
        return id
    # user_pw 형식 확인
    @field_validator("user_pw")
    @classmethod
    def check_pw_length(cls: Type["WithdrawReq"], pw: str) -> str:
        if not (8 <= len(pw) <= 16):
            raise ValueError(WithdrawCode.INVALID_FORMAT.value.code)
        return pw

# 회원 탈퇴 Response.body
class WithdrawRes(BaseModel):
    status: str = Field(...)
    message: str = Field(...)
    code: str = Field(...)
