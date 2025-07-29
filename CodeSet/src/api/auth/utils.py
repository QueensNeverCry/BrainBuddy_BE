from src.api.auth.response_code import CodeInfo, SignUpCode

ALL_AUTH_CODES = [SignUpCode] # LogInCode, TokenCode 추가 필요

def get_code_info(code: str) -> CodeInfo | None:
    for code_enum in ALL_AUTH_CODES:
        try:
            return code_enum[code].value
        except KeyError:
            continue
    return None