import secrets
from typing import Optional

from bs4 import BeautifulSoup
from fastapi import Depends, HTTPException, Request
from httpx import Response
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from .config import settings


templates = Jinja2Templates(directory=settings.templates_dir)


def csrf_html_response(request: Request, template_path: str, context: dict, status_code: int) -> HTMLResponse:
    """Adds csrf to a context and sets a cookie"""

    csrf_token = secrets.token_urlsafe(32)
    context["csrf_token"] = csrf_token
    response = templates.TemplateResponse(request, template_path, context, status_code=status_code)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
        path="/",
    )
    return response


def get_csrf_from_response(response: Response):
    """Gets value of <input type="hidden" name="csrf_token" value="{{ csrf_token }}">"""
    soup = BeautifulSoup(response.text, "html.parser")
    csrf_input = soup.find("input", {"name": "csrf_token"})
    csrf_token = csrf_input["value"]

    return csrf_token


async def get_csrf_token_from_cookie(request: Request) -> Optional[str]:
    return request.cookies.get("csrf_token")


async def get_csrf_token_from_form(request: Request) -> Optional[str]:
    form_data = await request.form()
    return form_data.get("csrf_token")


def validate_csrf(
    cookie_csrf_token: str = Depends(get_csrf_token_from_cookie),
    form_csrf_token: str = Depends(get_csrf_token_from_form),
) -> bool:
    if not cookie_csrf_token or not form_csrf_token:
        raise HTTPException(status_code=403, detail="Missing CSRF token")
    if form_csrf_token != cookie_csrf_token:
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    return True
