from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from pydantic import field_validator
import os

from .logger import logger

ENVIRONMENT = os.getenv("ENVIRONMENT")
logger.info(f"🏰 Environment: {ENVIRONMENT}")
if ENVIRONMENT == "development":
    load_dotenv()

BASE_DIR = Path(__file__).parent.parent

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")


class AuthJWTSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False,
    )

    private_key_path: Path
    public_key_path: Path
    algorithm: str = "RS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    # jwt_issuer: str = "my-fastapi-app"
    # jwt_audience: str = "my-fastapi-api"

    @field_validator('private_key_path', 'public_key_path')
    @classmethod
    def resolve_and_validate_key_paths(cls, v: Path) -> Path:
        # Resolve relative paths
        if not v.is_absolute():
            v = BASE_DIR / v

        # For tests, don't validate existence
        if os.getenv("ENVIRONMENT") == "test":
            return v  # Skip validation in tests

        if not v.exists():
            raise ValueError(f"Key file not found: {v}")
        return v


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False,
    )

    app_name: str = "Todo API"
    debug: bool
    templates_dir: str
    environment: str
    database_url: str

    auth_jwt: AuthJWTSettings = AuthJWTSettings()


settings = Settings()
