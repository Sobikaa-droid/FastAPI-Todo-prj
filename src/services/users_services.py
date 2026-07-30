import secrets
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import users_schemas
from ..models.users_models import User
from ..auth import utils
from ..dependencies import users_deps
from ..exceptions import users_exceptions

"""
All the functions that work with data
"""


async def create_user(db: AsyncSession, user_create_data: users_schemas.UserCreate) -> User:
    email_exists = await users_deps.user_exists(db, 'email', str(user_create_data.email))
    username_exists = await users_deps.user_exists(db, 'username', user_create_data.username)

    if email_exists or username_exists:
        raise users_exceptions.UserAlreadyExistsError()

    db_user = User(
        username=user_create_data.username,
        hashed_password=utils.hash_password(user_create_data.password),
        email=str(user_create_data.email),
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


async def authenticate_user(db: AsyncSession, user_auth_data: users_schemas.UserAuthenticationBase) -> Optional[User]:
    db_user = await users_deps.get_user_by_username(db, user_auth_data.username)

    # MUST compare passwords in constant time.
    dummy_hash = "$2b$12$" + secrets.token_hex(22)
    hashed_to_compare = db_user.hashed_password if db_user else dummy_hash
    is_valid = utils.validate_password(password=user_auth_data.password, hashed_password=hashed_to_compare)
    if not is_valid or not db_user:
        raise users_exceptions.InvalidUserCredentialsError()
    return db_user