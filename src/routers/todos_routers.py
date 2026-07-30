from fastapi import Depends, APIRouter, Request, responses, Form, Query
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from fastapi.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from .. import database, exc_handlers, csrf
from ..dependencies import todos_deps, users_deps
from ..schemas import todos_schemas
from ..services import todos_services
from ..models.users_models import User as UserModel
from ..config import settings


router = APIRouter(
    tags=["todos"],
)
templates = Jinja2Templates(directory=settings.templates_dir)


@router.get("/todos", response_class=HTMLResponse, include_in_schema=False)
async def read_todos(
    request: Request,
    filter_val: Optional[str] = Query(None),
    is_ascending: bool = Query(False),
    page_num: int = Query(1, ge=1),
    paginate_by_num: int = Query(5, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(database.get_db),
    alert: Optional[str] = None,
    current_user: UserModel = Depends(users_deps.get_current_user),
):
    todos = await todos_deps.get_paginated_user_todos(
        user_model=current_user,
        db=db,
        page_num=page_num,
        paginate_by_num=paginate_by_num,
        filter_val=filter_val,
        is_ascending=is_ascending,
    )

    context = {
        "request": request,
        "todos": todos.get('items'),
        "todos_amount": todos.get('items_amount'),
        "paginator": todos.get('paginator'),
        "current_user": current_user,
        "filter_val": filter_val,
        "alert": alert,
        "is_ascending": is_ascending,
    }
    return templates.TemplateResponse(request, "todos/todos.html", context)


@router.get("/todos/create", response_class=HTMLResponse, include_in_schema=False)
async def create_todo_form(
    request: Request,
    current_user: UserModel = Depends(users_deps.get_current_user),
    alert: Optional[str] = None,
):
    context = {
        "request": request,
        "current_user": current_user,
        "alert": alert,
    }
    return csrf.csrf_html_response(request, "todos/todo_create.html", context, status_code=200)


@router.post("/todos/create", response_class=HTMLResponse, include_in_schema=False)
async def create_todo(
    request: Request,
    title: str = Form(...),
    description: Optional[str] = Form(default=None),
    important: bool = Form(default=False),
    db: AsyncSession = Depends(database.get_db),
    current_user: UserModel = Depends(users_deps.get_current_user),
    _csrf_valid: bool = Depends(csrf.validate_csrf),
):
    try:
        todo_create_data = todos_schemas.TodoCreate(
            title=title,
            description=description,
            important=important,
        )
        await todos_services.create_todo(db=db, todo_create_data=todo_create_data, user_model=current_user)
        response = responses.RedirectResponse(
            "/todos?alert=Item+Successfully+Created", status_code=303
        )
        return response
    except ValidationError as e:
        errors = exc_handlers.get_validation_error_msg(e)

    context = {
        "request": request,
        "current_user": current_user,
        "errors": errors,
        "title": title,
        "description": description,
        "important": important,
    }
    return csrf.csrf_html_response(request, "todos/todo_create.html", context, status_code=422)


@router.get("/todos/{todo_pk}", response_class=HTMLResponse, include_in_schema=False)
async def read_todo(
    request: Request,
    todo_pk: int,
    db: AsyncSession = Depends(database.get_db),
    alert: Optional[str] = None,
    current_user: UserModel = Depends(users_deps.get_current_user),
):
    todo = await todos_deps.get_todo_by_pk(db=db, todo_pk=todo_pk, user_model=current_user)

    context = {
        "todo": todo,
        "request": request,
        "current_user": current_user,
        "alert": alert,
    }
    return csrf.csrf_html_response(request, "todos/todo_detail.html", context, status_code=200)


@router.get("/todos/{todo_pk}/edit", response_class=HTMLResponse, include_in_schema=False)
async def edit_todo_form(
    request: Request,
    todo_pk: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: UserModel = Depends(users_deps.get_current_user),
):
    todo = await todos_deps.get_todo_by_pk(db=db, todo_pk=todo_pk, user_model=current_user)

    context = {
        "request": request,
        "todo": todo,
        "current_user": current_user,
    }
    return csrf.csrf_html_response(request, "todos/todo_edit.html", context, status_code=200)


@router.post("/todos/{todo_pk}/edit", response_class=HTMLResponse, include_in_schema=False)
async def edit_todo(
    request: Request,
    todo_pk: int,
    title: Optional[str] = Form(default=None),
    description: Optional[str] = Form(default=None),
    important: bool = Form(False),
    db: AsyncSession = Depends(database.get_db),
    current_user: UserModel = Depends(users_deps.get_current_user),
    _csrf_valid: bool = Depends(csrf.validate_csrf),
):
    try:
        todo_update_data = todos_schemas.TodoUpdate(
            title=title,
            description=description,
            important=important,
        )
        await todos_services.update_todo(
            db=db,
            todo_update_data=todo_update_data,
            user_model=current_user,
            todo_pk=todo_pk
        )
        return responses.RedirectResponse(
            f"/todos/{todo_pk}?alert=Item+Successfully+Updated", status_code=303
        )
    except ValidationError as e:
        errors = exc_handlers.get_validation_error_msg(e)

    todo = await todos_deps.get_todo_by_pk(db=db, todo_pk=todo_pk, user_model=current_user)
    context = {
        "todo": todo,
        "request": request,
        "current_user": current_user,
        "errors": errors,
        "title": title,
        "description": description,
        "important": important,
    }
    return csrf.csrf_html_response(request, "todos/todo_edit.html", context, status_code=422)


@router.post("/todos/{todo_pk}/complete", include_in_schema=False)
async def complete_todo(
    todo_pk: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: UserModel = Depends(users_deps.get_current_user),
    _csrf_valid: bool = Depends(csrf.validate_csrf),
):
    await todos_services.complete_todo(db=db, todo_pk=todo_pk, user_model=current_user)
    response = responses.RedirectResponse(
        f"/todos/{todo_pk}?alert=Todo+completed", status_code=303
    )
    return response


@router.post("/todos/{todo_pk}/delete", include_in_schema=False)
async def delete_todo(
    todo_pk: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: UserModel = Depends(users_deps.get_current_user),
    _csrf_valid: bool = Depends(csrf.validate_csrf),
):
    await todos_services.delete_todo(db=db, todo_pk=todo_pk, user_model=current_user)
    response = responses.RedirectResponse(
        "/todos/?alert=Item+Successfully+Deleted", status_code=303
    )
    return response
