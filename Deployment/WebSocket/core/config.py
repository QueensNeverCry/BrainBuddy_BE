import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
ISSUER = os.getenv("ISSUER")
COOKIE_TIME = int(os.getenv("BB_COOKIE_TIME"))

ACCESS = os.getenv("ACCESS")
ACCESS_TYPE = os.getenv("ACCESS_TYPE")
ACCESS_TOKEN_EXPIRE_SEC= int(os.getenv("BB_ACCESS_TOKEN_EXPIRE_SEC"))

REFRESH = os.getenv("REFRESH")
REFRESH_TYPE = os.getenv("REFRESH_TYPE")
REFRESH_TOKEN_EXPIRE_SEC = int(os.getenv("BB_REFRESH_TOKEN_EXPIRE_SEC"))

LOCAL = os.getenv("localhost")

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
BLACK_LIST_ID = int(os.getenv("BLACK_LIST_ID"))
EXIST = int(os.getenv("EXIST"))

MYSQL_DB_URL = os.getenv("MYSQL_DB_URL")

TIME_OUT = int(os.getenv("TIME_OUT"))
N_FRAMES = int(os.getenv("N_FRAMES"))
FRAME_DIR = os.getenv("FRAME_DIR")
MODEL_PATH = os.getenv("MODEL_PATH")