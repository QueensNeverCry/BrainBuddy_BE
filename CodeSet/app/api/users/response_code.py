from typing import NamedTuple
from enum import Enum

class CodeInfo(NamedTuple):
    code: str
    message: str
    status: int


# --- TotalScore, DailyScore DB 관련 ---
class ScoreDB(Enum):
    SERVER_ERROR    = CodeInfo("SERVER_ERR", "Internal server error. Please try again later.", 500)
    BAD_GATEWAY     = CodeInfo("BAD_GATEWAY","A server gateway error occurred. Please try again later.",502)
    INVALID_FORMAT  = CodeInfo("INVALID_FORMAT", "Invalid format.", 422)