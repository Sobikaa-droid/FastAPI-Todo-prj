import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.todos_models import Todo as TodoModel
from ..models.users_models import User as UserModel
from ..schemas import todos_schemas
from ..dependencies.todos_deps import get_todo_by_pk
from ..exceptions import todos_exceptions


async def create_todo(
        db: AsyncSession,
        todo_create_data: todos_schemas.TodoCreate,
        user_model: UserModel
) -> TodoModel:
    db_todo = TodoModel(**todo_create_data.model_dump(), user=user_model)
    db.add(db_todo)
    await db.commit()
    await db.refresh(db_todo)

    return db_todo


async def update_todo(
        db: AsyncSession,
        todo_pk: int,
        todo_update_data: todos_schemas.TodoUpdate,
        user_model: UserModel,
) -> TodoModel:
    db_todo = await get_todo_by_pk(db=db, todo_pk=todo_pk, user_model=user_model)
    for key, val in todo_update_data.model_dump(exclude_unset=True).items():
        setattr(db_todo, key, val)
    await db.commit()
    await db.refresh(db_todo)

    return db_todo


async def complete_todo(
        db: AsyncSession,
        todo_pk: int,
        user_model: UserModel
) -> TodoModel:
    db_todo = await get_todo_by_pk(db=db, todo_pk=todo_pk, user_model=user_model)

    if db_todo.completed_date:
        raise todos_exceptions.TodoAlreadyCompletedError("Todo is already completed")

    db_todo.completed_date = datetime.datetime.now(datetime.UTC)
    await db.commit()
    await db.refresh(db_todo)

    return db_todo


async def delete_todo(
        db: AsyncSession,
        todo_pk: int,
        user_model: UserModel
) -> TodoModel:
    db_todo = await get_todo_by_pk(db=db, todo_pk=todo_pk, user_model=user_model)
    await db.delete(db_todo)
    await db.commit()

    return db_todo