from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.templating import Jinja2Templates

from .exceptions import todos_exceptions
from fastapi import Request, HTTPException, responses

from .logger import logger


templates = Jinja2Templates(directory="templates")


async def todo_not_found_exception_handler(request: Request, exc: todos_exceptions.TodoNotFoundError):
    context = {
        "request": request,
    }
    return templates.TemplateResponse(request, "errors/404.html", context, status_code=404)


async def unauthorized_exception_handler(exc: HTTPException):
    if exc.status_code == 401:
        return responses.RedirectResponse("/users/login", status_code=303)
    return exc


async def http_exception_handler(request: Request, exc: HTTPException):
    context = {
        "request": request,
        "status_code": exc.status_code,
        "err_msg": exc.detail,
    }
    return templates.TemplateResponse(request, "errors/generic_http.html", context, status_code=exc.status_code)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    message = "Validation errors:"
    for error in exc.errors():
        message += f"\nField: {error['loc']}, Error: {error['msg']}"
    context = {
        "request": request,
        "err_msg": message,
    }
    return templates.TemplateResponse(request, "errors/400.html", context, status_code=400)


def get_validation_error_msg(exc: ValidationError) -> list[str]:
    logger.error(f"❗ Validation error: {exc}")
    errors = []
    errors_list = exc.errors()
    for item in errors_list:
        field = item.get("loc", [""])[0]
        msg = item.get("msg", "Validation error")
        errors.append(f"{field}: {msg}")

    return errors
