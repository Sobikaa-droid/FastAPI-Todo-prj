import datetime
import bcrypt
import jwt
from typing import Optional, Dict, Any, Union
from functools import lru_cache
from fastapi import Request, Response

from ..config import settings
from ..logger import logger
from ..exceptions import jwt_exceptions
from ..models.users_models import User


@lru_cache(maxsize=1)
def get_public_key() -> str:
    return settings.auth_jwt.public_key_path.read_text()


@lru_cache(maxsize=1)
def get_private_key() -> str:
    return settings.auth_jwt.private_key_path.read_text()


def encode_jwt(
        payload: Dict[str, Any],
        private_key: Optional[str] = None,
        algorithm: str = settings.auth_jwt.algorithm,
        expire_minutes: int = settings.auth_jwt.access_token_expire_minutes,
        expire_timedelta: Optional[datetime.timedelta] = None,
) -> str:
    if not private_key:
        private_key = get_private_key()

    # Create a copy to avoid modifying original payload
    to_encode = payload.copy()

    # Add iat
    now = datetime.datetime.now(datetime.UTC)
    to_encode.update({"iat": int(now.timestamp())})

    # Add exp
    if expire_timedelta is not None:
        expire = now + expire_timedelta
    else:
        expire = now + datetime.timedelta(minutes=expire_minutes)
    to_encode.update({"exp": int(expire.timestamp())})

    # Validate token existence and type
    token_type = to_encode.get("type")
    if not token_type:
        logger.error("❗ Missing JWT type")
        raise jwt_exceptions.JWTTypeError("Missing token type")
    if token_type not in ("access", "refresh"):
        logger.error(f"❗ Invalid JWT type: {token_type}")
        raise jwt_exceptions.JWTTypeError(f"Invalid token type: {token_type}")

    # Validate sub existence
    if "sub" not in to_encode:
        logger.error(f"❗ Missing subject")
        raise jwt_exceptions.JWTInvalidError("Invalid token: missing subject")

    try:
        encoded = jwt.encode(
            to_encode,
            private_key,
            algorithm=algorithm,
        )

        # PyJWT returns string, but handle bytes for safety
        if isinstance(encoded, bytes):
            encoded = encoded.decode('utf-8')

        return encoded
    except Exception as e:
        logger.error(f"❗ JWT encoding failed: {e}")
        raise jwt_exceptions.JWTEncodeError(f"Failed to encode JWT: {e}")


def decode_jwt(
        token: str,
        public_key: str = None,
        algorithm: str = settings.auth_jwt.algorithm,
) -> Dict[str, Any]:

    if not token:
        raise jwt_exceptions.JWTMissingError()

    if not public_key:
        public_key = get_public_key()

    try:
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=[algorithm],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True,
                "require": ["exp", "sub", "type"]
            }
        )
    except jwt.ExpiredSignatureError:
        raise jwt_exceptions.JWTExpiredError()
    except jwt.InvalidTokenError as e:
        raise jwt_exceptions.JWTInvalidError(str(e))
    except Exception as e:
        logger.error(f"❗ JWT decode failed: {e}")
        raise jwt_exceptions.JWTDecodeError(f"Failed to decode JWT: {e}")

    token_type = decoded.get("type")
    if token_type not in ("access", "refresh"):
        logger.error(f"❗ Invalid JWT type: {token_type}")
        raise jwt_exceptions.JWTTypeError(f"Invalid token type: {token_type}")

    return decoded


def create_token(user_instance: User, token_type: str) -> str:
    """Generate a new refresh or access token for a user."""
    expire_timedelta = datetime.timedelta(minutes=15) if token_type == "access" else datetime.timedelta(days=7)

    return encode_jwt(
        payload={
            "sub": str(user_instance.pk),
            "type": token_type,
            "username": user_instance.username,
        },
        expire_timedelta=expire_timedelta
    )


def create_access_token(user_instance: User) -> str:
    return create_token(user_instance, "access")


def create_refresh_token(user_instance: User) -> str:
    return create_token(user_instance, "refresh")


def hash_password(password: str) -> bytes:
    salt = bcrypt.gensalt()
    password_bytes: bytes = password.encode("utf-8")
    return bcrypt.hashpw(password_bytes, salt)


def validate_password(password: Union[str, bytes], hashed_password: Union[str, bytes]) -> bool:
    if isinstance(password, str):
        password = password.encode("utf-8")
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode("utf-8")

    try:
        return bcrypt.checkpw(password, hashed_password)
    except (ValueError, TypeError):
        logger.error("❗ Password verification failed - invalid hash format or password type")
        return False


def set_auth_token_cookies(
    request: Request,
    response: Response,
    token_access: str,
    token_refresh: str,
):
    secure = request.url.scheme == "https"
    response.set_cookie(
        key="access_token",
        value=token_access,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=60 * 15,  # 15 minutes
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=token_refresh,
        httponly=True,
        secure=secure,
        samesite="strict",
        max_age=60 * 60 * 24 * 7,  # 7 days
        path="/",
    )
