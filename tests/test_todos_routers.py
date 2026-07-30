async def test_create_todo_success(async_client, log_user_in, todo_csrf_token):
    todo_create_data = {
        "csrf_token": todo_csrf_token,
        "title": "Test Title",
        "description": "Some test description",
        "important": True,
    }
    response = await async_client.post("/todos/create", data=todo_create_data)

    assert response.status_code == 303
    assert response.headers["location"] == "/todos?alert=Item+Successfully+Created"


async def test_read_todo_success(async_client, log_user_in, test_todo):
    todos_response = await async_client.get(f"/todos/{test_todo.pk}")
    assert todos_response.status_code == 200


async def test_edit_todo_success(async_client, test_todo, log_user_in, todo_csrf_token):
    todo_update_data = {
        "csrf_token": todo_csrf_token,
        "title": "Test Updated Title",
        "description": "Some updated test description",
        "important": False,
    }
    response = await async_client.post(f"/todos/{test_todo.pk}/edit", data=todo_update_data)

    assert response.status_code == 303
    assert response.headers["location"] == f"/todos/{test_todo.pk}?alert=Item+Successfully+Updated"


async def test_complete_todo_success(async_client, test_todo, log_user_in, todo_csrf_token):
    todo_complete_data = {
        "csrf_token": todo_csrf_token,
    }
    response = await async_client.post(f"/todos/{test_todo.pk}/complete", data=todo_complete_data)

    assert response.status_code == 303
    assert response.headers["location"] == f"/todos/{test_todo.pk}?alert=Todo+completed"


async def test_delete_todo_success(async_client, test_todo, log_user_in, todo_csrf_token):
    todo_data = {
        "csrf_token": todo_csrf_token,
    }
    response = await async_client.post(f"/todos/{test_todo.pk}/delete", data=todo_data)

    assert response.status_code == 303
    assert response.headers["location"] == f"/todos/?alert=Item+Successfully+Deleted"
