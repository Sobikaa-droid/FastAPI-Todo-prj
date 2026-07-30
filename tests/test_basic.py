from bs4 import BeautifulSoup

from src.csrf import get_csrf_from_response


def test_basic_math():
    """Simple test to verify pytest works."""
    assert 1 + 1 == 2


async def test_database_connection(test_db):
    from sqlalchemy import text

    result = await test_db.execute(text("SELECT 1"))
    value = result.scalar()

    assert value == 1


async def test_health_endpoint(async_client):
    """Test the health check endpoint."""
    response = await async_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


async def test_full_user_journey(async_client):
    # 1. Register
    response = await async_client.get("/users/register")
    assert response.status_code == 200

    register_data = {
        "username": "BiggestUser",
        "email": "biggestuser@gmail.com",
        "password": "BiggestTestPwd34_567",
        "csrf_token": get_csrf_from_response(response),
    }
    post_response = await async_client.post("/users/register", data=register_data)
    assert post_response.status_code == 303

    # 2. Login
    response = await async_client.get("/users/login")
    assert response.status_code == 200

    login_data = {
        "username": "BiggestUser",
        "password": "BiggestTestPwd34_567",
        "csrf_token": get_csrf_from_response(response),
    }
    post_response = await async_client.post("/users/login", data=login_data)
    assert post_response.status_code == 303

    # 3. Create t0do
    response = await async_client.get("/todos/create")
    assert response.status_code == 200

    todo_create_data = {
        "title": "Test Title",
        "description": "Some test description",
        "important": True,
        "csrf_token": get_csrf_from_response(response),
    }
    post_response = await async_client.post("/todos/create", data=todo_create_data)
    assert post_response.status_code == 303

    # 4. Edit t0do
    todo_pk = 1
    response = await async_client.get(f"/todos/{todo_pk}/edit")
    assert response.status_code == 200

    todo_update_data = {
        "title": "Test Title 1000",
        "description": "Some another description",
        "important": False,
        "csrf_token": get_csrf_from_response(response),
    }
    post_response = await async_client.post(f"/todos/{todo_pk}/edit", data=todo_update_data)
    assert post_response.status_code == 303

    # 5. Log out
    post_response = await async_client.post("/users/logout")
    assert post_response.status_code == 303






