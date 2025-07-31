from typing import NamedTuple
from enum import Enum

class CodeInfo(NamedTuple):
    code: str
    message: str
    status: int

# --- 토큰 인증 ---
class TokenAuth(Enum):
    TOKEN_EXPIRED = CodeInfo("TOKEN_EXPIRED", "Authentication token has expired.", 401)
    LOGIN_AGAIN     = CodeInfo("LOGIN_AGAIN", "Your tokens are expired. Please login again.", 401)
    TOKEN_INVALID = CodeInfo("TOKEN_INVALID", "Invalid authentication token.", 403)
    INSUFFICIENT_SCOPE  = CodeInfo("INSUFFICIENT_SCOPE", "Insufficient token scope for this resource.", 403)
    DECODE_ERROR = CodeInfo(code="DECODE_ERROR", message="There was an error while decoding token. Please try later.", status=500)
    SERVER_ERROR    = CodeInfo("SERVER_ERR", "Internal server error. Please try again later.", 500)

