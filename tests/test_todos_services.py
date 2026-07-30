import pytest
from sqlalchemy import select

from src.schemas.todos_schemas import TodoCreate, TodoUpdate
from src.services import todos_services, users_services
from src.exceptions import todos_exceptions
from src.models.todos_models import Todo as TodoModel


async def test_todo_fixture_values(test_todo):
    assert test_todo.title == "test todo"
    assert test_todo.description is None
    assert test_todo.important is False
    assert test_todo.user_pk is not None


async def test_update_todo_success(test_db, test_user, test_todo):
    todo_update_data = TodoUpdate(
        title="test todo updated",
        description="test description updated",
        important=True,
    )
    updated_todo = await todos_services.update_todo(
        db=test_db,
        todo_pk=test_todo.pk,
        todo_update_data=todo_update_data,
        user_model=test_user,
    )

    assert updated_todo.title == "test todo updated"
    assert updated_todo.description == "test description updated"
    assert updated_todo.important == True


async def test_update_todo_not_found(test_db, test_user):
    nonexistent_pk = 99
    todo_update_data = TodoUpdate(
        title="test todo updated",
        description="test description updated",
        important=True,
    )
    with pytest.raises(todos_exceptions.TodoNotFoundError) as exc_info:
        await todos_services.update_todo(
            db=test_db,
            todo_pk=nonexistent_pk,
            todo_update_data=todo_update_data,
            user_model=test_user,
        )

    assert f"Todo {nonexistent_pk} not found" in str(exc_info.value)


async def test_complete_todo_success(test_db, test_user, test_todo):
    completed_todo = await todos_services.complete_todo(
        db=test_db,
        todo_pk=test_todo.pk,
        user_model=test_user,
    )

    assert completed_todo.completed_date is not None


async def test_complete_todo_not_found(test_db, test_user):
    nonexistent_pk = 99
    with pytest.raises(todos_exceptions.TodoNotFoundError) as exc_info:
        await todos_services.complete_todo(
            db=test_db,
            todo_pk=nonexistent_pk,
            user_model=test_user
        )

    assert f"Todo {nonexistent_pk} not found" in str(exc_info.value)


async def test_complete_todo_already_completed(test_db, test_user, test_todo):
    await todos_services.complete_todo(
        db=test_db,
        todo_pk=test_todo.pk,
        user_model=test_user
    )
    with pytest.raises(todos_exceptions.TodoAlreadyCompletedError) as exc_info:
        await todos_services.complete_todo(
            db=test_db,
            todo_pk=test_todo.pk,
            user_model=test_user
        )

    assert "Todo is already completed" in str(exc_info.value)


async def test_delete_todo_success(test_db, test_user, test_todo):
    deleted_todo = await todos_services.delete_todo(test_db, test_todo.pk, test_user)

    assert deleted_todo.pk == test_todo.pk
    assert deleted_todo.title == "test todo"

    result = await test_db.execute(
        select(TodoModel).where(TodoModel.pk == test_todo.pk)
    )
    assert result.scalar_one_or_none() is None


async def test_delete_todo_not_found(test_db, test_user):
    nonexistent_pk = 99
    with pytest.raises(todos_exceptions.TodoNotFoundError) as exc_info:
        await todos_services.delete_todo(test_db, nonexistent_pk, test_user)

    assert f"Todo {nonexistent_pk} not found" in str(exc_info.value)


async def test_delete_todo_already_deleted(test_db, test_todo, test_user):
    await todos_services.delete_todo(test_db, test_todo.pk, test_user)
    with pytest.raises(todos_exceptions.TodoNotFoundError) as exc_info:
        await todos_services.delete_todo(test_db, test_todo.pk, test_user)

    assert f"Todo {test_todo.pk} not found" in str(exc_info.value)


async def test_delete_todo_wrong_user(test_db, test_todo, another_user):
    with pytest.raises(todos_exceptions.TodoNotFoundError) as exc_info:
        await todos_services.delete_todo(test_db, test_todo.pk, another_user)

    assert f"Todo {test_todo.pk} not found" in str(exc_info.value)

    result = await test_db.execute(
        select(TodoModel).where(TodoModel.pk == test_todo.pk)
    )
    todo = result.scalar_one_or_none()
    assert todo is not None
    assert todo.title == "test todo"

