# src/core/config.py
import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일을 프로젝트 시작 시 자동으로 환경변수로 로드

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
ACCESS = os.getenv("ACCESS")
ACCESS_TOKEN_EXPIRE_SEC= os.getenv("BB_ACCESS_TOKEN_EXPIRE_SEC")
REFRESH = os.getenv("REFRESH")
REFRESH_TOKEN_EXPIRE_SEC = os.getenv("BB_REFRESH_TOKEN_EXPIRE_SEC")
SAFE_SEC = os.getenv("BB_SAFE_SEC")
LOCAL = os.getenv("localhost")
REDIS_PORT = os.getenv("REDIS_PORT")
BLACK_LIST_ID = os.getenv("BLACK_LIST_ID")
EXIST = os.getenv("EXIST")
MYSQL_DB_URL = os.getenv("MYSQL_DB_URL")