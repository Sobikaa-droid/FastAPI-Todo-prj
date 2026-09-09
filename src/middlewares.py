from traceback import print_exception
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.templating import Jinja2Templates

from .logger import logger


templates = Jinja2Templates(directory="templates")


class CatchExceptionsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            logger.error(f"❗ Internal server error: {exc}", exc_info=True)
            print_exception(exc)
            context = {"request": request}
            return templates.TemplateResponse(request, "errors/500.html", context, status_code=500)


class AddSecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"

        return response


class RefreshAccessTokenMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        new_access_token = getattr(request.state, "new_access_token", None)
        if new_access_token:
            secure = request.url.scheme == "https"
            response.set_cookie(
                key="access_token",
                value=new_access_token,
                httponly=True,
                secure=secure,
                samesite="lax",
                max_age=60 * 15,  # 15 minutes
                path="/",
            )

        return response


# async def catch_exceptions_middleware(request: Request, call_next):
#     """This is an exception handler middleware. It handles all the internal server errors."""
#     try:
#         return await call_next(request)
#     except Exception as exc:
#         logger.error(f"❗ Internal server error: {exc}", exc_info=True)
#         print_exception(exc)
#         context = {"request": request}
#         return templates.TemplateResponse(request, "errors/500.html", context, status_code=500)


# async def add_security_headers_middleware(request: Request, call_next):
#     response = await call_next(request)
#
#     response.headers["X-Frame-Options"] = "DENY"
#     response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
#
#     return response


# async def refresh_token_middleware(request: Request, call_next):
#     """Takes NAT from request.state and sets an AT with the value of NAT."""
#     response = await call_next(request)
#
#     new_access_token = getattr(request.state, "new_access_token", None)
#     if new_access_token:
#         secure = request.url.scheme == "https"
#         response.set_cookie(
#             key="access_token",
#             value=new_access_token,
#             httponly=True,
#             secure=secure,
#             samesite="lax",
#             max_age=60 * 15,  # 15 minutes
#             path="/",
#         )
#
#     return response
