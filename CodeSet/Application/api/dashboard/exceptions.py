from fastapi import HTTPException, status
from typing import NamedTuple
from enum import Enum

class ErrorMetadata(NamedTuple):
    code: str
    message: str
    http_status: int


class User(Enum):
    INVALID_USER = ErrorMetadata("INVALID_USER",
                                 "You are not valid user.",
                                 status.HTTP_403_FORBIDDEN)
    
    def exc(self) -> HTTPException:
        code, message, http_status = self.value
        return HTTPException(status_code=http_status,
                             detail={"code": code, "message": message})

class Score(Enum):
    INVALID_FORMAT  = ErrorMetadata("INVALID_FORMAT", 
                                    "Invalid format.", 
                                    status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    def exc(self) -> HTTPException:
        code, message, http_status = self.value
        return HTTPException(status_code=http_status,
                             detail={"code": code, "message": message})
    

class Daily(Enum):
    INVALID_FORMAT  = ErrorMetadata("INVALID_FORMAT", 
                                    "Invalid format.", 
                                    422)
    FORBIDDEN       = ErrorMetadata("FORBIDDEN",
                                    "That was a rather convoluted request.",
                                    status.HTTP_403_FORBIDDEN)

    def exc(self) -> HTTPException:
        code, message, http_status = self.value
        return HTTPException(status_code=http_status,
                             detail={"code": code, "message": message})