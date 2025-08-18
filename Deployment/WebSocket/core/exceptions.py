from enum import Enum

class TokenVerdict(Enum):
    VALID = (1000, "Hello, there !!!")
    INVALID_TOKEN = (4001, "Invalid tokens.") # landing page 로..
    ACCESS_TOKEN_EXPIRED = (4002, "Access token expired.") # refresh 요청으로..
    REFRESH_TOKEN_EXPIRED = (4003, "Refresh token expired.") # 재로그인으로..

    @property
    def code(self):
        return self.value[0]

    @property
    def reason(self):
        return self.value[1]