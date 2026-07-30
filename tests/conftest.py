import asyncio
import secrets

import pytest
import os

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool


# Setup paths
load_dotenv(".env.test")


from src.logger import logger


# Get test database URL (with fallback)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://test_user:test_password@localhost:5433/test_db"
)

# Set as DATABASE_URL for app imports
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
logger.info(f"ℹ️ TEST_DATABASE_URL: {TEST_DATABASE_URL}")


from src.main import app
from src.database import Base, get_db
from src.schemas import users_schemas, todos_schemas
from src.services import users_services, todos_services


# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool
)

TestAsyncSession = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestAsyncSession() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def test_user(test_db):
    user_create_data = users_schemas.UserCreate(
        username="testuser",
        email="test@example.com",
        password="TestPassword34_229",
    )
    created_user = await users_services.create_user(db=test_db, user_create_data=user_create_data)
    return created_user


@pytest.fixture
async def another_user(test_db):
    user_create_data = users_schemas.UserCreate(
        username="anothertestuser",
        email="anothertest@example.com",
        password="AnotherTestPassword34_229",
    )
    created_user = await users_services.create_user(db=test_db, user_create_data=user_create_data)
    return created_user


@pytest.fixture
def test_csrf_token(async_client):
    token = secrets.token_urlsafe(32)
    async_client.cookies.set("csrf_token", token)
    return token


@pytest.fixture
def todo_csrf_token(async_client):
    token = secrets.token_urlsafe(32)
    async_client.cookies.set("csrf_token", token)
    return token


@pytest.fixture
async def log_user_in(async_client, test_user, test_csrf_token):
    user_login_data = {
        "csrf_token": test_csrf_token,
        "username": test_user.username,
        "password": "TestPassword34_229"
    }
    await async_client.post("/users/login", data=user_login_data)


@pytest.fixture
async def test_todo(test_db, test_user):
    todo_create_data = todos_schemas.TodoCreate(
        title="test todo",
    )
    created_todo = await todos_services.create_todo(
        db=test_db,
        todo_create_data=todo_create_data,
        user_model=test_user,
    )
    return created_todo


@pytest.fixture
async def another_todo(test_db, another_user):
    todo_create_data = todos_schemas.TodoCreate(
        title="another test todo",
    )
    created_todo = await todos_services.create_todo(
        db=test_db,
        todo_create_data=todo_create_data,
        user_model=another_user,
    )
    return created_todo


# @pytest.fixture
# def get_csrf_token(async_client):
#     """Fixture that returns a function to fetch csrf token"""
#     async def _get_csrf_token(url_path):
#         response = await async_client.get(url_path)
#         assert response.status_code == 200
#
#         soup = BeautifulSoup(response.text, "html.parser")
#         csrf_input = soup.find("input", {"name": "csrf_token"})
#         assert csrf_input is not None
#
#         return csrf_input.get("value")
#
#     return _get_csrf_token


# @pytest.fixture
# def bypass_csrf(monkeypatch):
#     """Bypass CSRF validation for all tests that use this fixture."""
#     def mock_validate_csrf(cookie_csrf_token, form_csrf_token):
#         return True
#
#     monkeypatch.setattr(
#         "src.dependencies.users_deps.validate_csrf",
#         mock_validate_csrf
#     )


@pytest.fixture(scope="function")
async def async_client(test_db):
    async def override_get_db():
        async with TestAsyncSession() as session:  # Fresh session!
            yield session

    app.dependency_overrides = {get_db: override_get_db}

    # async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
    #     yield client
    #
    # app.dependency_overrides.clear()

    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    yield client

    await client.aclose()
    app.dependency_overrides.clear()