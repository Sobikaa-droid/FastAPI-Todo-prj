from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import settings


DATABASE_URL = settings.database_url

# TODO add database monitoring
async_engine = create_async_engine(
    DATABASE_URL,
    echo=settings.debug,
    pool_size=5,
    max_overflow=5,
    pool_timeout=10,
    pool_recycle=1800,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
