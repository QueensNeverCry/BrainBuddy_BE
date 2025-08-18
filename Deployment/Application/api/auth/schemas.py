from pydantic import BaseModel, EmailStr, SecretStr
from pydantic import Field, model_validator, field_validator
from typing import Type, Dict, Any
import hmac, re

from Application.api.auth.exceptions import SignUp, Login, Withdraw


NamePattern = r'^[A-Za-z0-9가-힣_-]{2,16}$'


# 회원가입 api/auth/sign-up ---------------------------------------------------------
    # 회원가입 Request.body DTO
class SignUpRequest(BaseModel):
    email: str = Field(...)
    user_name: str = Field(...)
    user_pw: SecretStr = Field(...)
    user_pw_confirm: SecretStr = Field(...)
    
        # Endpoint 도달 전, pydantic 모델로 schema 검증 : 모든 field 값 존재 확인
    @model_validator(mode="before")
    @classmethod
    def check_fields(cls: Type["SignUpRequest"], values: Dict[str, Any]) -> Dict[str, Any]:
        required_fields = ["user_name", "email", "user_pw", "user_pw_confirm"]
        missing = [f for f in required_fields if f not in values or values[f] in (None, '')]
        if missing: # 필수값이 하나라도 누락시, app 로 에러 반환
            raise SignUp.INVALID_FORMAT.exc()
        return values
    
        # Endpoint 도달 전, pydantic 모델로 schema 검증 : email 형식 검사
    @field_validator("email")
    @classmethod
    def check_email_length(cls: Type["SignUpRequest"], email: str) -> str:
        if not (5 <= len(email) <= 32):
            raise SignUp.INVALID_FORMAT.exc()
        return email
        # Endpoint 도달 전, pydantic 모델로 schema 검증 : user_name 형식 검사
    @field_validator("user_name")
    @classmethod
    def check_name_length(cls: Type["SignUpRequest"], user_name: str) -> str:
        if not (2 <= len(user_name) <= 16):
            raise SignUp.INVALID_FORMAT.exc()
        if not re.match(NamePattern, user_name):
            raise SignUp.INVALID_FORMAT.exc()
        return user_name
        # Endpoint 도달 전, pydantic 모델로 schema 검증 : user_pw 형식 검사
    @field_validator("user_pw")
    @classmethod
    def check_pw_length(cls: Type["SignUpRequest"], pw: SecretStr) -> SecretStr:
        if not (8 <= len(pw.get_secret_value()) <= 24):
            raise SignUp.INVALID_FORMAT.exc()
        return pw
        # Endpoint 도달 전, pydantic 모델로 schema 검증 : user_pw_confirm 형식 검사
    @field_validator("user_pw_confirm")
    @classmethod
    def check_pw_confirm_length(cls: Type["SignUpRequest"], pw_confirm: SecretStr) -> SecretStr:
        if not (8 <= len(pw_confirm.get_secret_value()) <= 24):
            raise SignUp.INVALID_FORMAT.exc()
        return pw_confirm
    
        # Endpoint 도달 전, pydantic 모델로 검증 : pw 와 pw_confirm 일치 확인
    @model_validator(mode="after")
    def check_password_match(self):
        pw = self.user_pw.get_secret_value()
        pw_confirm = self.user_pw_confirm.get_secret_value()
        if not hmac.compare_digest(pw, pw_confirm):
            raise SignUp.INVALID_PW.exc()
        return self
    

    # 회원가입 성공 Response.body DTO
class SignUpResponse(BaseModel):
    status: str = Field("success")
    user_name: str = Field(..., min_length=2)
    message: str = Field("Sign-Up Completed.")
    code: str = Field("CREATED")
# ---------------------------------------------------------------------------------



# 로그인 api/auth/log-in -----------------------------------------------------------
    # 로그인 Request.body DTO
class LogInRequest(BaseModel):
    email: str = Field(...)
    user_pw: SecretStr = Field(...)

        # Endpoint 도달 전, pydantic 모델로 schema 검증 : 모든 field 값 존재 확인
    @model_validator(mode="before")
    @classmethod
    def check_all_fields_exist(cls: Type["LogInRequest"], values: Dict[str, Any]) -> Dict[str, Any]:
        required_fields = ["email", "user_pw"]
        missing = [f for f in required_fields if f not in values or values[f] in (None, '')]
        if missing:
            raise Login.WRONG_FORMAT.exc()
        return values
    
        # Endpoint 도달 전, pydantic 모델로 schema 검증 : email 길이 검사
    @field_validator("email")
    @classmethod
    def check_email_length(cls: Type["LogInRequest"], email: str) -> str:
        if not (5 <= len(email) <= 32):
            raise Login.WRONG_FORMAT.exc()
        return email
        # Endpoint 도달 전, pydantic 모델로 schema 검증 : user_pw 길이 검사
    @field_validator("user_pw")
    @classmethod
    def check_pw_length(cls: Type["LogInRequest"], pw: SecretStr) -> SecretStr:
        if not (8 <= len(pw.get_secret_value()) <= 24):
            raise Login.WRONG_FORMAT.exc()
        return pw
    

    # 로그인 성공 Response.body DTO
class LogInResponse(BaseModel):
    status: str = Field("success")
    user_name: str = Field(...)
    message: str = Field("Login Completed.")
    code: str = Field("LOGIN_SUCCESS")
# ---------------------------------------------------------------------------------



# 토큰 갱신 api/auth/refresh ---------------------------------------------------------
    # 토큰 갱신 성공 Response.body DTO
class RenewResponse(BaseModel):
    status: str = Field("success")
    message: str = Field("Token refreshed successfully.")
    code: str = Field("REFRESHED")
# ----------------------------------------------------------------------------------



# 로그아웃 api/auth/log-out ----------------------------------------------------------
    # 로그아웃 Response.body DTO
class LogOutResponse(BaseModel):
    status: str = Field("success")
    message: str = Field("You have been logged out successfully.")
    code: str = Field("LOGOUT")
# ----------------------------------------------------------------------------------



# 회원탈퇴 api/auth/withdraw ----------------------------------------------------------
    # 회원탈퇴 Request.body DTO
class WithdrawRequest(BaseModel):
    email: str = Field(...)
    user_pw: SecretStr = Field(...)

        # Endpoint 도달 전, pydantic 모델로 schema 검증 : 모든 field 값 존재 확인
    @model_validator(mode="before")
    @classmethod
    def check_fields(cls: Type["WithdrawRequest"], values: Dict[str, Any]) -> Dict[str, Any]:
        required_fields = ["email", "user_pw"]
        missing = [f for f in required_fields if f not in values or values[f] in (None, '')]
        if missing:
            raise Withdraw.INVALID_FORMAT.exc()
        return values
        # Endpoint 도달 전, pydantic 모델로 schema 검증 : 모든 email 형식 확인
    @field_validator("email")
    @classmethod
    def check_email_length(cls: Type["WithdrawRequest"], email: str) -> str:
        if not (5 <= len(email) <= 32):
            raise Withdraw.INVALID_FORMAT.exc()
        return email
        # Endpoint 도달 전, pydantic 모델로 schema 검증 : 모든 user_pw 형식 확인
    @field_validator("user_pw")
    @classmethod
    def check_pw_length(cls: Type["WithdrawRequest"], pw: SecretStr) -> SecretStr:
        if not (8 <= len(pw.get_secret_value()) <= 24):
            raise Withdraw.INVALID_FORMAT.exc()
        return pw


    # 회원탈퇴 Response.body DTO
class WithdrawResponse(BaseModel):
    status: str = Field("success")
    message: str = Field("Account successfully withdrawn.")
    code: str = Field("WITHDRAW")
# ----------------------------------------------------------------------------------