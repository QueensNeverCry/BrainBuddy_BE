import os
from dotenv import load_dotenv

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(base_dir, ".env")
load_dotenv(dotenv_path=dotenv_path)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
ISSUER = "KSEB_04"
ACCESS = os.getenv("ACCESS")
ACCESS_TYPE = "queen"
ACCESS_TOKEN_EXPIRE_SEC= int(os.getenv("BB_ACCESS_TOKEN_EXPIRE_SEC"))
REFRESH = os.getenv("REFRESH")
REFRESH_TYPE = "nevercry"
REFRESH_TOKEN_EXPIRE_SEC = int(os.getenv("BB_REFRESH_TOKEN_EXPIRE_SEC"))
LOCAL = os.getenv("localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
BLACK_LIST_ID = int(os.getenv("BLACK_LIST_ID"))
EXIST = int(os.getenv("EXIST"))
MYSQL_DB_URL = os.getenv("MYSQL_DB_URL")
LOCAL_DB_URL = os.getenv("LOCAL_DB_URL")

TIME_OUT = 30
N_FRAMES = 30
FRAME_DIR = ""
MODEL_PATH = ""