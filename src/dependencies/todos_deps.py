from typing import Optional
from sqlalchemy import select, func, Select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.todos_models import Todo as TodoModel
from ..models.users_models import User as UserModel
from ..exceptions import todos_exceptions


async def get_todo_by_pk(
        db: AsyncSession,
        todo_pk: int,
        user_model: UserModel
) -> Optional[TodoModel]:
    result = await db.execute(
        select(TodoModel).where(TodoModel.pk == todo_pk, TodoModel.user == user_model)
    )
    db_todo = result.scalar_one_or_none()
    if not db_todo:
        raise todos_exceptions.TodoNotFoundError(f"Todo {todo_pk} not found")
    return db_todo


def filter_and_order_todo_query(
        todo_query,
        filter_val: str | None = None,
        is_ascending: bool = False,
) -> Select:
    # Order
    if is_ascending:
        query = todo_query.order_by(TodoModel.creation_date.asc())
    else:
        query = todo_query.order_by(TodoModel.creation_date.desc())

    # Filter
    if filter_val == "not_completed":
        query = query.where(TodoModel.completed_date.is_(None))
    elif filter_val == "completed":
        query = query.where(TodoModel.completed_date.is_not(None))
    elif filter_val == "important":
        query = query.where(TodoModel.important.is_(True))

    return query


async def get_paginated_user_todos(
        db: AsyncSession,
        user_model: UserModel,
        filter_val: str | None = None,
        is_ascending: bool = True,
        page_num: int = 1,
        paginate_by_num: int = 10
) -> dict:
    base_query = select(TodoModel).where(TodoModel.user_pk == user_model.pk)

    # Filter query
    filtered_query = filter_and_order_todo_query(base_query, filter_val, is_ascending)

    # Paginate items
    paginated_query = filtered_query.offset(
        (page_num - 1) * paginate_by_num
    ).limit(paginate_by_num)
    items_result = await db.execute(paginated_query)
    todos = items_result.scalars().all()

    # Count the filtered query
    count_query = select(func.count()).select_from(filtered_query.subquery())
    count_result = await db.execute(count_query)
    try:
        todos_amount = count_result.scalar_one()
    except NoResultFound:
        todos_amount = 0

    # Count pages
    pages_amount = max(1, (todos_amount + paginate_by_num - 1) // paginate_by_num)

    return {
        "items": todos,
        "items_amount": todos_amount,
        "paginator": {
            "page_num": page_num,
            "pages_amount": pages_amount,
            "paginate_by_num": paginate_by_num,
        }
    }
