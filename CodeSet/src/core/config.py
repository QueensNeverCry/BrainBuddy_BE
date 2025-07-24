# src/core/config.py
import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일을 프로젝트 시작 시 자동으로 환경변수로 로드

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_SEC= os.getenv("ACCESS_TOKEN_EXPIRE_SEC")
ACCESS = os.getenv("BB_ACCESS_TOKEN")
REFRESHED = os.getenv("BB_REFRESHED_TOKEN")
LOCAL=os.getenv("localhost")
REDIS_PORT=os.getenv("REDIS_PORT")
BLACK_LIST_ID=os.getenv("BLACK_LIST_ID")
EXIST=os.getenv("EXIST")