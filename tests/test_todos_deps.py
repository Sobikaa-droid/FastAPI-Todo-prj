import pytest
from sqlalchemy import select, func

from src.dependencies import todos_deps
from src.services import todos_services
from src.schemas import todos_schemas
from src.models.todos_models import Todo as TodoModel
from src.exceptions import todos_exceptions


async def test_get_todo_by_pk_not_found(test_db, test_user):
    pk = 999
    with pytest.raises(todos_exceptions.TodoNotFoundError) as exc_info:
        await todos_deps.get_todo_by_pk(db=test_db, todo_pk=999, user_model=test_user)

    assert exc_info.value.message == f"Todo {pk} not found"


async def test_get_todo_by_pk_idor(test_db, test_user, another_todo):
    with pytest.raises(todos_exceptions.TodoNotFoundError) as exc_info:
        await todos_deps.get_todo_by_pk(db=test_db, todo_pk=another_todo.pk, user_model=test_user)

    assert exc_info.value.message == f"Todo {another_todo.pk} not found"


async def test_filter_and_order_todo_query_success(test_db, test_user):
    for i in range(5):
        important_value = i >= 2
        todo_data = todos_schemas.TodoCreate(
            title=f"test todo {i + 1}",
            description=f"Description {i + 1}",
            important=important_value
        )
        await todos_services.create_todo(
            db=test_db,
            todo_create_data=todo_data,
            user_model=test_user
        )

    todo_query = select(TodoModel).where(TodoModel.user_pk == test_user.pk)
    filtered_query = todos_deps.filter_and_order_todo_query(
        todo_query=todo_query,
        filter_val="important",
        is_ascending=True
    )
    result = await test_db.execute(filtered_query)
    assert result.scalars().first().title == "test todo 3"

    count_stmt = select(func.count()).select_from(filtered_query.subquery())
    count_result = await test_db.execute(count_stmt)
    count = count_result.scalar()
    assert count == 3


async def test_get_paginated_user_todos_success(test_db, test_user):
    for i in range(10):
        todo_data = todos_schemas.TodoCreate(
            title=f"test todo {i + 1}",
            description=f"Description {i + 1}",
            important=False
        )
        await todos_services.create_todo(
            db=test_db,
            todo_create_data=todo_data,
            user_model=test_user
        )

    paginate_by_num = 3

    result = await todos_deps.get_paginated_user_todos(
        db=test_db,
        user_model=test_user,
        page_num=1,
        paginate_by_num=paginate_by_num
    )

    assert result["items_amount"] == 10
    assert result["paginator"]["pages_amount"] == 4
    assert result["paginator"]["page_num"] == 1
    assert result["paginator"]["paginate_by_num"] == 3

    assert len(result["items"]) == 3
    assert result["items"][0].title == "test todo 1"
    assert result["items"][paginate_by_num - 1].title == "test todo 3"

    result_page2 = await todos_deps.get_paginated_user_todos(
        db=test_db,
        user_model=test_user,
        page_num=2,
        paginate_by_num=paginate_by_num
    )

    assert len(result_page2["items"]) == 3
    assert result_page2["items"][0].title == "test todo 4"
    assert result_page2["items"][paginate_by_num - 1].title == "test todo 6"
    assert result_page2["paginator"]["page_num"] == 2


async def test_get_paginated_user_todos_empty(test_db, test_user):
    result = await todos_deps.get_paginated_user_todos(
        db=test_db,
        user_model=test_user,
        page_num=1,
        paginate_by_num=5
    )

    assert result["items_amount"] == 0
    assert result["paginator"]["pages_amount"] == 1
    assert result["paginator"]["page_num"] == 1
    assert result["paginator"]["paginate_by_num"] == 5
    assert len(result["items"]) == 0


async def test_get_paginated_user_todos_filter_important(test_db, test_user):
    for i in range(5):
        important_val = i >= 3
        todo_data = todos_schemas.TodoCreate(
            title=f"test todo {i + 1}",
            description=f"Description {i + 1}",
            important=important_val
        )
        await todos_services.create_todo(
            db=test_db,
            todo_create_data=todo_data,
            user_model=test_user
        )

    result = await todos_deps.get_paginated_user_todos(
        db=test_db,
        user_model=test_user,
        filter_val="important",
        page_num=1,
        paginate_by_num=5,
    )

    assert result["items_amount"] == 2
    assert result["paginator"]["pages_amount"] == 1
    assert result["paginator"]["page_num"] == 1
    assert len(result["items"]) == 2
    assert all(todo.important for todo in result["items"])


async def test_get_paginated_user_todos_sort_ascending(test_db, test_user):
    for i in range(10):
        todo_data = todos_schemas.TodoCreate(
            title=f"test todo {i + 1}",
            description=f"Description {i + 1}",
            important=False,
        )
        await todos_services.create_todo(
            db=test_db,
            todo_create_data=todo_data,
            user_model=test_user
        )

    result = await todos_deps.get_paginated_user_todos(
        db=test_db,
        user_model=test_user,
        is_ascending=False,
        page_num=1,
        paginate_by_num=5,
    )

    assert result["items"][0].title == "test todo 10"
    assert result["items"][4].title == "test todo 6"


async def test_get_paginated_user_todos_last_page(test_db, test_user):
    for i in range(5):
        todo_data = todos_schemas.TodoCreate(
            title=f"test todo {i + 1}",
            description=f"Description {i + 1}",
            important=False
        )
        await todos_services.create_todo(
            db=test_db,
            todo_create_data=todo_data,
            user_model=test_user
        )

    paginate_by_num = 2

    result = await todos_deps.get_paginated_user_todos(
        db=test_db,
        user_model=test_user,
        page_num=3,
        paginate_by_num=paginate_by_num,
    )

    assert result["items_amount"] == 5
    assert result["paginator"]["pages_amount"] == 3
    assert result["paginator"]["page_num"] == 3
    assert result["paginator"]["paginate_by_num"] == 2

    assert len(result["items"]) == 1
    assert result["items"][0].title == "test todo 5"


async def test_get_paginated_user_todos_page_out_of_range(test_db, test_user):
    for i in range(5):
        todo_data = todos_schemas.TodoCreate(
            title=f"test todo {i + 1}",
            description=f"Description {i + 1}",
            important=False
        )
        await todos_services.create_todo(
            db=test_db,
            todo_create_data=todo_data,
            user_model=test_user
        )

    paginate_by_num = 2

    result = await todos_deps.get_paginated_user_todos(
        db=test_db,
        user_model=test_user,
        page_num=4,
        paginate_by_num=paginate_by_num,
    )

    assert result["items_amount"] == 5
    assert result["paginator"]["pages_amount"] == 3
    assert result["paginator"]["page_num"] == 4
    assert result["paginator"]["paginate_by_num"] == 2

    assert len(result["items"]) == 0