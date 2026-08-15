from fastapi import Depends, Form, APIRouter, Request, responses
from fastapi.responses import HTMLResponse
from pydantic import ValidationError, EmailStr
from pydantic_core import PydanticCustomError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.templating import Jinja2Templates

from .. import database, exc_handlers, csrf
from ..services import users_services
from ..schemas import users_schemas
from ..auth import utils
from ..logger import logger
from ..exceptions import users_exceptions
from ..config import settings


router = APIRouter(
    tags=["users"],
)
templates = Jinja2Templates(directory=settings.templates_dir)


@router.get("/users/register", response_class=HTMLResponse, include_in_schema=False)
def register_form(request: Request) -> HTMLResponse:
    context = {
        "request": request,
    }
    return csrf.csrf_html_response(request, "users/register.html", context, status_code=200)


@router.post("/users/register", response_class=HTMLResponse, include_in_schema=False)
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    email: EmailStr = Form(...),
    db: AsyncSession = Depends(database.get_db),
    _csrf_valid: bool = Depends(csrf.validate_csrf),
):
    errors = []
    logger.info("Returning register post request...")

    try:
        user_create_data = users_schemas.UserCreate(
            username=username, email=email, password=password
        )
        created_user = await users_services.create_user(user_create_data=user_create_data, db=db)
        response = responses.RedirectResponse(
            url=f"/?alert=Registration+successful&username={created_user.username}",
            status_code=303,
        )
        return response
    except users_exceptions.UserAlreadyExistsError as e:
        logger.warning(f"⚠️ Registration failed: {e}")
        errors.append(str(e))
    except ValidationError as e:
        errors = exc_handlers.get_validation_error_msg(e)
    except PydanticCustomError as e:
        logger.error(f"❗ PydanticCustomError: {e}")
        errors.append(str(e.message_template))

    context = {
        "request": request,
        "errors": errors,
        "username": username,
        "email": email,
    }
    return csrf.csrf_html_response(request, "users/register.html", context, status_code=422)


@router.get("/users/login", include_in_schema=False)
def login_form(request: Request) -> HTMLResponse:
    context = {
        "request": request,
    }
    logger.info("Rendering login form...")
    return csrf.csrf_html_response(request, "users/login.html", context, status_code=200)


@router.post("/users/login", response_class=HTMLResponse, include_in_schema=False)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(database.get_db),
    _csrf_valid: bool = Depends(csrf.validate_csrf),
):
    errors = []

    try:
        user_login_data = users_schemas.UserLogin(
            username=username, password=password
        )
        db_user = await users_services.authenticate_user(user_auth_data=user_login_data, db=db)

        token_access = utils.create_access_token(user_instance=db_user)
        token_refresh = utils.create_refresh_token(user_instance=db_user)

        response = responses.RedirectResponse(f"/?alert=Welcome+Back+{db_user.username}", status_code=303)

        utils.set_auth_token_cookies(request, response, token_access, token_refresh)
        return response
    except users_exceptions.InvalidUserCredentialsError as e:
        logger.warning(f"⚠️ Failed login attempt for username: {username}")
        status_code = 401
        errors.append(str(e))
    except ValidationError as e:
        status_code = 422
        errors = exc_handlers.get_validation_error_msg(e)
    except PydanticCustomError as e:
        logger.error(f"❗ PydanticCustomError: {e}")
        status_code = 422
        errors.append(str(e.message_template))

    context = {
        "request": request,
        "errors": errors,
        "username": username,
    }
    return csrf.csrf_html_response(request, "users/login.html", context, status_code=status_code)


@router.post("/users/logout", include_in_schema=False)
async def logout(request: Request):
    response = responses.RedirectResponse("/?alert=Successfully+logged+out", status_code=303)
    secure = request.url.scheme == "https"

    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/"
    )
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=secure,
        samesite="strict",
        path="/"
    )
    response.delete_cookie(
        key="csrf_token",
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/"
    )

    return response
