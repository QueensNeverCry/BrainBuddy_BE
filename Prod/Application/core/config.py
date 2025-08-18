import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
ISSUER = os.getenv("KSEB_04")
ACCESS = os.getenv("ACCESS")
ACCESS_TYPE = os.getenv("queen")
ACCESS_TOKEN_EXPIRE_SEC= int(os.getenv("BB_ACCESS_TOKEN_EXPIRE_SEC"))
REFRESH = os.getenv("REFRESH")
REFRESH_TYPE = os.getenv("nevercry")
REFRESH_TOKEN_EXPIRE_SEC = int(os.getenv("BB_REFRESH_TOKEN_EXPIRE_SEC"))
EXIST = int(os.getenv("EXIST"))

LOCAL = os.getenv("localhost")

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
BLACK_LIST_ID = int(os.getenv("BLACK_LIST_ID"))

LOCAL_DB_URL = os.getenv("LOCAL_DB_URL")
MYSQL_DB_URL = os.getenv("MYSQL_DB_URL")

COMPONENT_CNT = int(os.getenv("COMPONENT_CNT"))
STUDY_TIME_THRESHOLD = int(os.getenv("STUDY_TIME_THRESHOLD"))