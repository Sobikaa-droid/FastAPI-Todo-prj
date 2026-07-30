from pydantic import BaseModel, EmailStr, Field, field_validator
from email_validator import validate_email, EmailNotValidError
from password_validator import PasswordValidator
from pydantic_core import PydanticCustomError


class UserAuthenticationBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v) -> str:
        reserved_names = ["admin", "root", "system", "null", "undefined", "staff", "moderator"]
        username = v.strip()
        if username in reserved_names:
            raise PydanticCustomError(
                "invalid_username",
                "Invalid username format: {error}",
                {"error": f"Username '{username}' not allowed"}
            )
        return username

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        validator = PasswordValidator()
        validator \
            .min(8) \
            .max(255) \
            .has().uppercase() \
            .has().lowercase() \
            .has().digits() \
            .has().symbols() \
            .has().no().spaces()

        if not validator.validate(v):
            e = ("Password must be 8-255 characters and include: "
                 "uppercase, lowercase, number, symbol, no spaces")
            raise PydanticCustomError(
                "invalid_password",
                "invalid password format: {error}",
                {"error": str(e)}
            )

        return v


class UserCreate(UserAuthenticationBase):
    email: EmailStr

    @field_validator('email')
    @classmethod
    def validate_email(cls, v) -> str:
        try:
            validated = validate_email(v, check_deliverability=False)
            return validated.normalized.lower()
        except EmailNotValidError as e:
            raise PydanticCustomError(
                "invalid_email",
                "Invalid email format: {error}",
                {"error": str(e)}
            ) from e


class UserLogin(UserAuthenticationBase):
    pass
