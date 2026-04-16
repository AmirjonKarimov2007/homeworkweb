import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "testsecret")
os.environ.setdefault("JWT_REFRESH_SECRET", "testrefresh")

import pytest
from httpx import AsyncClient
from app.main import app
from app.db.session import engine, AsyncSessionLocal
from app.models import Base


@pytest.fixture(scope="session", autouse=True)
async def prepare_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture()
async def client():
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
