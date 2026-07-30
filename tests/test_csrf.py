import pytest
from bs4 import BeautifulSoup
from fastapi import HTTPException

from src.csrf import validate_csrf


async def test_validate_csrf_success(async_client):
    response = await async_client.get("/users/register")

    csrf_token_cookie = response.cookies.get("csrf_token")

    soup = BeautifulSoup(response.text, "html.parser")
    csrf_input = soup.find("input", {"name": "csrf_token"})
    csrf_token_form = csrf_input["value"]

    assert validate_csrf(cookie_csrf_token=csrf_token_cookie, form_csrf_token=csrf_token_form) is True


async def test_validate_csrf_invalid(async_client):
    response = await async_client.get("/users/register")

    csrf_token_cookie = response.cookies.get("csrf_token")
    csrf_token_form = "INVALID"

    with pytest.raises(HTTPException) as exc_info:
        validate_csrf(cookie_csrf_token=csrf_token_cookie, form_csrf_token=csrf_token_form)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Invalid CSRF token"


async def test_validate_csrf_missing(async_client):
    csrf_token_cookie = None
    csrf_token_form = None

    with pytest.raises(HTTPException) as exc_info:
        validate_csrf(cookie_csrf_token=csrf_token_cookie, form_csrf_token=csrf_token_form)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Missing CSRF token"