from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import MYSQL_DB_URL

engine = create_engine(MYSQL_DB_URL, pool_pre_ping=True)
UsersSession = sessionmaker(autocommit= False, autoflush= False, bind= engine)