from fastapi import HTTPException, status
from typing import NamedTuple
from enum import Enum

class ErrorMetadata(NamedTuple):
    code: str
    message: str
    http_status: int


# 회원가입 실패 Enum
class SignUp(Enum):
    INVALID_REQ     = ErrorMetadata("INVALID_REQ",
                                    "Invalid request.",
                                    status.HTTP_400_BAD_REQUEST)
    FORBIDDEN       = ErrorMetadata("FORBIDDEN", 
                                    "SSIBAL !!! ", 
                                    status.HTTP_403_FORBIDDEN)
    USER_EXISTS     = ErrorMetadata("USER_EXISTS", 
                                    "User ID or Name already exists.", 
                                    status.HTTP_409_CONFLICT)
    INVALID_FORMAT  = ErrorMetadata("INVALID_FORMAT",
                                    "Invalid field(s). Please write again.",
                                    status.HTTP_422_UNPROCESSABLE_ENTITY)
    INVALID_PW      = ErrorMetadata("INVALID_PW",
                                    "Password does not meet requirements.",
                                    status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    def exc(self) -> HTTPException:
        code, message, http_status = self.value
        return HTTPException(status_code=http_status,
                             detail={"code": code, "message": message})
    

# 로그인 실패 Enum
class Login(Enum):
    INVALID_REQ     = ErrorMetadata("INVALID_REQ",
                                    "Invalid request.",
                                    status.HTTP_400_BAD_REQUEST)
    WRONG_FORMAT    = ErrorMetadata("WRONG_FORMAT",
                                    "Invalid email or password.",
                                    status.HTTP_401_UNAUTHORIZED)
    BANNED          = ErrorMetadata("BANNED",
                                    "Banned User.",
                                    status.HTTP_403_FORBIDDEN)
    USER_NOT_FOUND  = ErrorMetadata("USER_NOT_FOUND",
                                    "No registered user found.",
                                    status.HTTP_404_NOT_FOUND)

    def exc(self) -> HTTPException:
        code, message, http_status = self.value
        return HTTPException(status_code=http_status,
                             detail={"code": code, "message": message})


# 회원탈퇴 실패 Enum
class Withdraw(Enum):
    INVALID_FORMAT  = ErrorMetadata("INVALID_FORMAT",
                                    "Invalid ID or Name format.",
                                    status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    def exc(self) -> HTTPException:
        code, message, http_status = self.value
        return HTTPException(status_code=http_status,
                             detail={"code": code, "message": message})