import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi_sqlalchemy_monitor import SQLAlchemyMonitor
from fastapi_sqlalchemy_monitor.action import PrintStatistics, WarnMaxTotalInvocation

from . import database, exc_handlers, middlewares
from .routers import users_routers, todos_routers
from .dependencies import users_deps
from .config import settings
from .dependencies import jinja_filters
from .logger import logger
from .exceptions import todos_exceptions
from .models.users_models import User as UserModel


logger.info(f"ℹ️ DATABASE_URL: {database.DATABASE_URL}")


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    async with database.async_engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)
    yield
    await database.async_engine.dispose()


def start_application() -> FastAPI:
    fastapi_app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
        version="1.0.0",
        docs_url="/docs" if settings.debug else None
    )
    return fastapi_app


# FastAPI
app = start_application()


# Middlewares
app.add_middleware(
    SQLAlchemyMonitor,
    engine=database.async_engine,
    actions=[
        PrintStatistics(),  # See query stats in console
        WarnMaxTotalInvocation(max_invocations=10),  # Alert on >10 queries
    ]
)
app.add_middleware(middlewares.CatchExceptionsMiddleware)
app.add_middleware(middlewares.AddSecurityHeadersMiddleware)
app.add_middleware(middlewares.RefreshAccessTokenMiddleware)


# Routers
app.include_router(users_routers.router)
app.include_router(todos_routers.router)


# Exception handlers
app.add_exception_handler(
    todos_exceptions.TodoNotFoundError,
    exc_handlers.todo_not_found_exception_handler,
)
app.add_exception_handler(
    RequestValidationError,
    exc_handlers.validation_exception_handler,
)
app.add_exception_handler(
    HTTPException,
    exc_handlers.unauthorized_exception_handler,
)
app.add_exception_handler(
    HTTPException,
    exc_handlers.http_exception_handler,
)


# Jinja
templates = Jinja2Templates(directory=settings.templates_dir)
templates.env.filters["strptime"] = jinja_filters.strptime_filter
templates.env.filters["strftime"] = jinja_filters.strftime_filter
templates.env.filters["url_with"] = jinja_filters.url_with_params


# Routers
@app.get("/health")
async def health():
    logger.info("Health check called")
    return {"status": "healthy"}


@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    current_user: UserModel = Depends(users_deps.get_optional_user),
    alert: str = None
) -> HTMLResponse:
    context = {
        "request": request,
        "current_user": current_user,
        "alert": alert,
        "is_authenticated": current_user is not None,
    }
    return templates.TemplateResponse(request, "home.html", context)


if __name__ == "__main__":
    uvicorn.run("src.main:app", reload=True)
