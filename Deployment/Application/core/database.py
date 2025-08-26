from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

from Application.core.config import MYSQL_DB_URL, DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_TIMEOUT, DB_POOL_RECYCLE

# 비동기 엔진(async engine) 생성
# 실제 AWS 운영 DB
async_engine = create_async_engine(url=MYSQL_DB_URL,
                                   pool_pre_ping=True,
                                   pool_size=DB_POOL_SIZE,
                                   max_overflow=DB_MAX_OVERFLOW,
                                   pool_timeout=DB_POOL_TIMEOUT,
                                   pool_recycle=DB_POOL_RECYCLE)

# 비동기 세션 메이커(async_sessionmaker) 생성
AsyncSessionLocal = async_sessionmaker( bind=async_engine,     # bind the async engine
                                        class_=AsyncSession,   # 세션 클래스 지정
                                        expire_on_commit=False, # 커밋 후 객체 만료 방지
                                        autoflush=False )        # 자동 flush 비활성화

# UsersAsyncSession = AsyncSessionLocal
# RefreshTokensAsyncSession = AsyncSessionLocal
# ScoreTablesAsyncSession = AsyncSessionLocal