from unittest.mock import patch


async def test_register_success(async_client, test_csrf_token):
    register_data = {
        "csrf_token": test_csrf_token,
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword34_229",
    }

    response = await async_client.post("/users/register", data=register_data)

    assert response.status_code == 303
    assert response.headers["location"] == "/?alert=Registration+successful&username=testuser"


async def test_register_duplicate_user(async_client, test_csrf_token):
    register_data = {
        "csrf_token": test_csrf_token,
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword34_229",
    }

    await async_client.post("/users/register", data=register_data)
    response = await async_client.post("/users/register", data=register_data)

    assert response.status_code == 422
    assert "User with such credentials already exists." in response.text


async def test_login_success(async_client, test_user, test_csrf_token):
    user_login_data = {
        "csrf_token": test_csrf_token,
        "username": test_user.username,
        "password": "TestPassword34_229",
    }
    response = await async_client.post("/users/login", data=user_login_data)

    assert response.status_code == 303
    assert response.headers["location"] == "/?alert=Welcome+Back+testuser"

    cookies = response.cookies
    assert "access_token" in cookies
    assert "refresh_token" in cookies

    set_cookie = response.headers.get("set-cookie", "")
    assert "Max-Age=900" in set_cookie or "max-age=900" in set_cookie


async def test_login_user_not_found(async_client, test_csrf_token):
    user_login_data = {
        "csrf_token": test_csrf_token,
        "username": "testuserwrong",
        "password": "TestWrongPassword34_229",
    }
    response = await async_client.post("/users/login", data=user_login_data)

    assert response.status_code == 401
    assert "Invalid username/password." in response.text


async def test_logout(async_client, test_user, test_csrf_token):
    user_login_data = {
        "csrf_token": test_csrf_token,
        "username": test_user.username,
        "password": "TestPassword34_229",
    }
    login_response = await async_client.post("/users/login", data=user_login_data)

    async_client.cookies = login_response.cookies

    logout_response = await async_client.post("/users/logout")
    assert logout_response.status_code == 303
    assert logout_response.headers["location"] == "/?alert=Successfully+logged+out"

    set_cookie_headers = logout_response.headers.get_list("set-cookie")
    assert len(set_cookie_headers) == 3
    assert any('access_token="";' in i for i in set_cookie_headers)
    assert any('refresh_token="";' in i for i in set_cookie_headers)
    assert any('csrf_token="";' in i for i in set_cookie_headers)
    assert all("Max-Age=0;" in i for i in set_cookie_headers)
