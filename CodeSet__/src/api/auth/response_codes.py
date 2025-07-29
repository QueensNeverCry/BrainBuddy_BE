# auth 관련 상수 (코드, 메시지)

class Status:
    SUCCESS = "success"
    FAIL = "fail"

class Code:
    CREATED = "CREATED"
    INVALID_REQ = "INVALID_REQ"
    USER_EXISTS = "USER_EXISTS"
    MISSING_REQ = "MISSING_REQ"
    INVALID_ID = "INVALID_ID"
    INVALID_PW = "INVALID_PW"
    SERVER_ERR = "SERVER_ERR"
    BAD_GATEWAY = "BAD_GATEWAY"

MESSAGES = { Code.CREATED: "Sign-Up Completed",
             Code.INVALID_REQ: "Invalid request.",
             Code.USER_EXISTS: "User ID already exists.",
             Code.MISSING_REQ: "Missing required field(s).",
             Code.INVALID_ID: "Invalid ID format.",
             Code.INVALID_PW: "Password does not meet requirements.",
             Code.SERVER_ERR: "Internal server error. Please try again later.",
             Code.BAD_GATEWAY: "A server gateway error occurred. Please try again later." }