from typing import Optional, Sequence
from fastapi import HTTPException, Request, Depends, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from ..models.users_models import User
from ..auth import utils
from ..exceptions import jwt_exceptions
from ..database import get_db
from ..logger import logger

"""
All the functions that get data
"""


async def user_exists(db: AsyncSession, field: str, value: str) -> bool:
    if field not in ["email", "username"]:
        raise ValueError(f"Invalid field: {field}.")

    result = await db.execute(
        select(User).where(getattr(User, field) == value.strip())
    )
    return result.scalar_one_or_none()


async def get_user_by_pk(db: AsyncSession, pk: int) -> Optional[User]:
    result = await db.execute(
        select(User).where(User.pk == pk)
    )
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()


async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> Sequence[User]:
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    return result.scalars().all()


async def get_access_token_from_cookie(request: Request) -> Optional[str]:
    return request.cookies.get("access_token")


async def get_refresh_token_from_cookie(request: Request) -> Optional[str]:
    return request.cookies.get("refresh_token")


async def get_current_user(
    request: Request,
    access_token: Optional[str] = Depends(get_access_token_from_cookie),
    refresh_token: Optional[str] = Depends(get_refresh_token_from_cookie),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Gets current user with AT and stores it in state OR gets user through state.
    If AT cookie is expired/gone, uses RT cookie to set a new AT to state.
    !!! Requires middleware to get new AT from state and set it as a cookie !!!
    Only use with routers that REQUIRE authentication.
    """
    if hasattr(request.state, "current_user"):
        return request.state.current_user
    async def validate_token_and_user(token: str) -> User:
        payload = utils.decode_jwt(token)
        sub = payload.get("sub")

        try:
            pk = int(sub)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user identifier format",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await get_user_by_pk(db, pk=pk)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers = {"WWW-Authenticate": "Bearer"},
            )
        if hasattr(user, 'is_active') and not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated",
            )

        request.state.current_user = user
        return user
    try:
        return await validate_token_and_user(access_token)
    except (jwt_exceptions.JWTExpiredError, jwt_exceptions.JWTMissingError):
        # Actions to get a new AT through an RT
        try:
            validated_user = await validate_token_and_user(refresh_token)
            new_access_token = utils.create_access_token(user_instance=validated_user)
            request.state.new_access_token = new_access_token  # Catch with a middleware and set a cookie
            return validated_user
        except (jwt_exceptions.JWTExpiredError,
                jwt_exceptions.JWTMissingError,
                jwt_exceptions.JWTInvalidError) as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt_exceptions.JWTInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    request: Request,
    access_token: Optional[str] = Depends(get_access_token_from_cookie),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Only use with routers that DON'T require authentication."""
    try:
        return await get_current_user(request=request, access_token=access_token, db=db)
    except HTTPException as e:
        return None
