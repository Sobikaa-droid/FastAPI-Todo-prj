import pytest
from datetime import timedelta

from bs4 import BeautifulSoup
from fastapi import Request, HTTPException
from unittest.mock import Mock

from src.dependencies.users_deps import get_current_user
from src.auth import utils
from src.logger import logger


async def test_get_current_user_success(test_db, test_user):
    mock_request = Mock(spec=Request)
    mock_request.state = Mock()

    token_access = utils.create_access_token(user_instance=test_user)
    token_refresh = utils.create_refresh_token(user_instance=test_user)

    current_user = await get_current_user(
        request=mock_request,
        access_token=token_access,
        refresh_token=token_refresh,
        db=test_db
    )

    assert current_user.username == "testuser"
    assert current_user.email == "test@example.com"
    assert current_user.hashed_password != "TestPassword34_229"
    assert len(current_user.hashed_password) > 20


async def test_get_current_user_sub_is_not_num(test_db, test_user):
    mock_request = Mock(spec=Request)
    mock_request.state = Mock()

    token_refresh = utils.create_refresh_token(user_instance=test_user)
    token_access = utils.encode_jwt(
        payload={
            "sub": "NOT_A_NUM",
            "type": "access",
        }
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            request=mock_request,
            access_token=token_access,
            refresh_token=token_refresh,
            db=test_db
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid user identifier format"


async def test_get_current_user_not_found(test_db, test_user):
    mock_request = Mock(spec=Request)
    mock_request.state = Mock()

    token_refresh = utils.create_refresh_token(user_instance=test_user)
    token_access = utils.encode_jwt(
        payload={
            "sub": str(12345),
            "type": "access",
        }
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            request=mock_request,
            access_token=token_access,
            refresh_token=token_refresh,
            db=test_db
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "User not found"


async def test_get_current_user_is_inactive(test_db, test_user):
    mock_request = Mock(spec=Request)
    mock_request.state = Mock()

    test_user.is_active = False

    await test_db.commit()
    await test_db.refresh(test_user)

    token_refresh = utils.create_refresh_token(user_instance=test_user)
    token_access = utils.encode_jwt(
        payload={
            "sub": str(test_user.pk),
            "type": "access",
        }
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            request=mock_request,
            access_token=token_access,
            refresh_token=token_refresh,
            db=test_db
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "User account is deactivated"


async def test_get_current_user_jwt_missing(test_db):
    mock_request = Mock(spec=Request)
    mock_request.state = Mock()

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            access_token=None,
            refresh_token=None,
            db=test_db,
            request=mock_request,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing token"


async def test_get_current_user_token_invalid(test_db):
    mock_request = Mock(spec=Request)
    mock_request.state = Mock()

    invalid_token_type = "INVALID"
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            access_token=invalid_token_type,
            refresh_token=invalid_token_type,
            db=test_db,
            request=mock_request,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token: Not enough segments"


async def test_get_current_user_all_tokens_expired(test_db, test_user):
    mock_request = Mock(spec=Request)
    mock_request.state = Mock()

    expired_token_access = utils.encode_jwt(
        payload={
            "sub": str(test_user.pk),
            "type": "access",
        },
        expire_timedelta=timedelta(seconds=-1)
    )
    expired_token_refresh = utils.encode_jwt(
        payload={
            "sub": str(test_user.pk),
            "type": "refresh",
        },
        expire_timedelta=timedelta(seconds=-1)
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            access_token=expired_token_access,
            refresh_token=expired_token_refresh,
            db=test_db,
            request=mock_request,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token is expired"


async def test_get_current_user_access_token_expired(test_db, test_user):
    # Should AT token through RT
    mock_request = Mock(spec=Request)
    mock_request.state = Mock()

    expired_token_access = utils.encode_jwt(
        payload={
            "sub": str(test_user.pk),
            "type": "access",
        },
        expire_timedelta=timedelta(seconds=-1)
    )
    token_refresh = utils.create_refresh_token(user_instance=test_user)

    current_user = await get_current_user(
        access_token=expired_token_access,
        refresh_token=token_refresh,
        db=test_db,
        request=mock_request,
    )

    assert current_user.username == "testuser"
    assert current_user.email == "test@example.com"
    assert current_user.hashed_password != "TestPassword34_229"
    assert len(current_user.hashed_password) > 20
