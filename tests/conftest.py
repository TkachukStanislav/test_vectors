import asyncio

import fakeredis
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app import (
    models,  # noqa: F401 — імпорт реєструє таблиці в Base.metadata
    worker,
)
from app.api import jobs as jobs_api
from app.config import settings
from app.db import Base, get_session
from app.main import app

# postgresql+asyncpg://user:pass@localhost:5432/mini_petp_db → ..._test
SERVER_URL, _, DB_NAME = settings.database_url.rpartition("/")
TEST_DB_NAME = f"{DB_NAME}_test"

test_engine = create_async_engine(f"{SERVER_URL}/{TEST_DB_NAME}", poolclass=NullPool)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)


async def create_test_db():
    admin = create_async_engine(
        f"{SERVER_URL}/postgres", isolation_level="AUTOCOMMIT", poolclass=NullPool
    )
    async with admin.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_DB_NAME}
        )
        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    await admin.dispose()

    async with test_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="session", autouse=True)
def prepare_test_db():
    asyncio.run(create_test_db())


async def override_get_session():
    async with TestSession() as session:
        yield session


@pytest.fixture
async def client():
    async with test_engine.begin() as conn:
        await conn.execute(text("TRUNCATE users, jobs RESTART IDENTITY CASCADE"))

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


class FakeTask:
    def __init__(self):
        self.calls = []

    def delay(self, *args):
        # запам'ятати виклик замість відправки в RabbitMQ
        self.calls.append(args)


@pytest.fixture(autouse=True)
def queued_jobs(monkeypatch):
    fake = FakeTask()
    monkeypatch.setattr(jobs_api, "process_job", fake)
    return fake


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    fake = fakeredis.FakeAsyncRedis(decode_responses=True)
    monkeypatch.setattr(jobs_api, "redis_client", fake)
    return fake


@pytest.fixture
async def user_id(client):
    response = await client.post("/users", json={"email": "owner@example.com"})
    return response.json()["id"]


@pytest.fixture
def worker_db(monkeypatch):
    engine = create_engine(
        f"{SERVER_URL}/{TEST_DB_NAME}".replace("+asyncpg", "+psycopg"), poolclass=NullPool
    )
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE users, jobs RESTART IDENTITY CASCADE"))
    monkeypatch.setattr(worker, "sync_engine", engine)
    monkeypatch.setattr(worker, "redis_sync", fakeredis.FakeRedis())
    monkeypatch.setattr(worker.time, "sleep", lambda seconds: None)
    yield engine
    engine.dispose()
