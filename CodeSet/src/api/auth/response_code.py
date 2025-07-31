from typing import NamedTuple
from enum import Enum

class CodeInfo(NamedTuple):
    code: str
    message: str
    status: int

# --- DB 관련 ---

# --- 회원가입 ---
class SignUpCode(Enum):
    CREATED = CodeInfo("CREATED", "Sign-Up Completed.", 201)
    INVALID_REQ = CodeInfo("INVALID_REQ", "Invalid request.", 400)
    FORBIDDEN = CodeInfo("FORBIDDEN", "SSIBAL !!! ", 403)
    USER_EXISTS = CodeInfo("USER_EXISTS", "User ID already exists.", 409)
    MISSING_REQ = CodeInfo("MISSING_REQ", "Missing required field(s).", 422)
    INVALID_FORMAT = CodeInfo("INVALID_FORMAT", "Invalid ID or Name format.", 422)
    INVALID_PW = CodeInfo("INVALID_PW", "Password does not meet requirements.", 422)
    SERVER_ERROR = CodeInfo("SERVER_ERR", "Internal server error. Please try later.", 500)
    BAD_GATEWAY = CodeInfo("BAD_GATEWAY", "A server gateway error occurred. Please try again later.", 502)

# --- 로그인(Login) ---
class LogInCode(Enum):
    LOGIN_SUCCESS   = CodeInfo("LOGIN_SUCCESS", "Log-In Completed.", 200)
    INVALID_REQ     = CodeInfo("INVALID_REQ", "Invalid request.", 400)
    WRONG_FORMAT  = CodeInfo("WRONG_FORMAT", "Invalid username or password.", 401)
    BANNED          = CodeInfo("BANNED", "Banned.", 403)
    USER_NOT_FOUND  = CodeInfo("USER_NOT_FOUND", "No registered user found.", 404)
    SERVER_ERROR    = CodeInfo("SERVER_ERR", "Internal server error. Please try again later.", 500)
    BAD_GATEWAY     = CodeInfo("BAD_GATEWAY","A server gateway error occurred. Please try again later.",502)

# --- 회원탈퇴 ---
class WithdrawCode(Enum):
    WITHDRAW = CodeInfo("WITHDRAW", message="Account successfully withdrawn.", status=200)
    MISSING_REQ = CodeInfo("MISSING_REQ", "Missing required field(s).", 422)
    INVALID_FORMAT = CodeInfo("INVALID_FORMAT", "Invalid ID or Name format.", 422)
    

# --- 토큰 DB 관련 ---
class TokenDB(Enum):
    SERVER_ERROR    = CodeInfo("SERVER_ERR", "Internal server error. Please try again later.", 500)
    BAD_GATEWAY     = CodeInfo("BAD_GATEWAY","A server gateway error occurred. Please try again later.",502)

# --- 토큰 인증 ---
class TokenAuth(Enum):
    REFRESHED = CodeInfo("REFRESHED", "Token refreshed successfully.", 200)
    TOKEN_EXPIRED = CodeInfo("TOKEN_EXPIRED", "Authentication token has expired.", 401)
    LOGIN_AGAIN     = CodeInfo("LOGIN_AGAIN", "Your tokens are expired. Please login again.", 401)
    TOKEN_INVALID = CodeInfo("TOKEN_INVALID", "Invalid authentication token.", 403)
    USER_NOT_FOUND  = CodeInfo("USER_NOT_FOUND", "No registered user found.", 404)
    INSUFFICIENT_SCOPE  = CodeInfo("INSUFFICIENT_SCOPE", "Insufficient token scope for this resource.", 403)
    SERVER_ERROR    = CodeInfo("SERVER_ERR", "Internal server error. Please try again later.", 500)