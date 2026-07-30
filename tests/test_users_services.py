import pytest
from sqlalchemy import select

from src.schemas.users_schemas import UserCreate, UserAuthenticationBase
from src.services.users_services import create_user, authenticate_user
from src.exceptions import users_exceptions
from src.models.users_models import User as UserModel
from src.logger import logger


async def test_create_user_success(test_db):
    user_create_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="TestPassword34_229",
    )

    created_user = await create_user(test_db, user_create_data)

    assert created_user.username == "testuser"
    assert created_user.email == "test@example.com"
    assert created_user.hashed_password != "TestPassword34_229"
    assert len(created_user.hashed_password) > 20


async def test_create_user_duplicate_username(test_db):
    user_create_data_1 = UserCreate(
        username="testuser",
        email="test@example.com",
        password="TestPassword34_229",
    )
    await create_user(test_db, user_create_data_1)

    user_create_data_2 = UserCreate(
        username="testuser",
        email="testother@example.com",
        password="TestPassword34_229",
    )

    with pytest.raises(users_exceptions.UserAlreadyExistsError):
        await create_user(test_db, user_create_data_2)

    result = await test_db.execute(select(UserModel).where(UserModel.username == "testuser"))
    users = result.scalars().all()
    assert len(users) == 1


async def test_create_user_duplicate_email(test_db):
    user_create_data_1 = UserCreate(
        username="testuser",
        email="test@example.com",
        password="TestPassword34_229",
    )
    await create_user(test_db, user_create_data_1)

    user_create_data_2 = UserCreate(
        username="testuserother",
        email="test@example.com",
        password="TestPassword34_229",
    )

    with pytest.raises(users_exceptions.UserAlreadyExistsError):
        await create_user(test_db, user_create_data_2)

    result = await test_db.execute(select(UserModel).where(UserModel.email == "test@example.com"))
    users = result.scalars().all()
    assert len(users) == 1


async def test_authenticate_user_success(test_db):
    user_create_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="TestPassword34_229",
    )
    await create_user(test_db, user_create_data)

    user_auth_data = UserAuthenticationBase(
        username=user_create_data.username,
        password=user_create_data.password,
    )
    authenticated_user = await authenticate_user(test_db, user_auth_data)

    assert authenticated_user.username == "testuser"
    assert authenticated_user.email == "test@example.com"
    assert authenticated_user.hashed_password != "TestPassword34_229"
    assert len(authenticated_user.hashed_password) > 20


async def test_authenticate_user_incorrect_password(test_db):
    user_create_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="TestPassword34_229",
    )
    await create_user(test_db, user_create_data)

    user_auth_data = UserAuthenticationBase(
        username=user_create_data.username,
        password="WrongPassword34_229",
    )

    with pytest.raises(users_exceptions.InvalidUserCredentialsError) as exc_info:
        await authenticate_user(test_db, user_auth_data)

    assert exc_info.value.message == "Invalid username/password."


async def test_authenticate_user_incorrect_username(test_db):
    user_create_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="TestPassword34_229",
    )
    await create_user(test_db, user_create_data)

    user_auth_data = UserAuthenticationBase(
        username="wrongusername",
        password=user_create_data.password,
    )
    with pytest.raises(users_exceptions.InvalidUserCredentialsError) as exc_info:
        await authenticate_user(test_db, user_auth_data)

    assert exc_info.value.message == "Invalid username/password."
