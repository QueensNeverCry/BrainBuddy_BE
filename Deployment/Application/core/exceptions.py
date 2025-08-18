from fastapi import HTTPException, status
from typing import NamedTuple
from enum import Enum

class ErrorMetadata(NamedTuple):
    code: str
    message: str
    http_status: int


# 내부 서버 로직 오류 ?
class Server(Enum):
    SERVER_ERROR    = ErrorMetadata("SERVER_ERR",
                                    "Internal server error. Please try again later.",
                                    status.HTTP_500_INTERNAL_SERVER_ERROR)
    DB_ERROR        = ErrorMetadata("DB_ERROR",
                                    "Maybe IntegrityError occured.",
                                    status.HTTP_500_INTERNAL_SERVER_ERROR)
    BAD_GATEWAY     = ErrorMetadata("BAD_GATEWAY",
                                    "A server gateway error occurred. Please try again later.",
                                    status.HTTP_502_BAD_GATEWAY)

    def exc(self) -> HTTPException:
        code, message, http_status = self.value
        return HTTPException(status_code=http_status,
                             detail={"code": code, "message": message})
    

# --- 토큰 인증 ---
class TokenAuth(Enum):
    TOKEN_EXPIRED   = ErrorMetadata("TOKEN_EXPIRED",
                                    "Authentication token has expired.",
                                    status.HTTP_401_UNAUTHORIZED)
    LOGIN_AGAIN     = ErrorMetadata("LOGIN_AGAIN",
                                    "Your tokens are expired. Please login again.",
                                    status.HTTP_401_UNAUTHORIZED)
    TOKEN_INVALID   = ErrorMetadata("TOKEN_INVALID",
                                    "Invalid authentication token.",
                                    status.HTTP_403_FORBIDDEN)
    USER_NOT_FOUND  = ErrorMetadata("USER_NOT_FOUND",
                                    "No registered user found.",
                                    status.HTTP_404_NOT_FOUND)
    INVALID_SCOPE   = ErrorMetadata("INVALID_SCOPE",
                                    "Insufficient token scope for this resource.",
                                    status.HTTP_406_NOT_ACCEPTABLE)

    def exc(self) -> HTTPException:
        code, message, http_status = self.value
        return HTTPException(status_code=http_status,
                             detail={"code": code, "message": message})