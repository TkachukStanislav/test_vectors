from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# 2. Створення рушія (Engine)
engine = create_async_engine(settings.database_url, echo=True)

# 3. Фабрика сесій
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


# 4. Базовий клас для моделей
class Base(DeclarativeBase):
    pass


# 5. Dependency для отримання асинхронної сесії
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session