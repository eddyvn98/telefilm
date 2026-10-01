from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True
    )

    PROJECT_NAME: str = "Telegram Film"
    API_V1_STR: str = "/api"

    # Telegram
    BOT_TOKEN: str = ""
    API_ID: int = 0
    API_HASH: str = ""
    STORAGE_CHANNEL_ID: str = ""
    WEBAPP_URL: str = ""
    UPLOAD_SPEED_LIMIT_MB: float = 0.0 # 0 means unlimited
    ALLOWED_TELEGRAM_IDS: str = "" # Comma-separated list of IDs
    ADMIN_TELEGRAM_IDS: str = "" # Comma-separated admin IDs; empty = no admin access

    # Filesystem safety
    UPLOAD_ROOTS: str = "" # Comma-separated absolute roots allowed for admin scan/upload

    # Security
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 1 week
    STREAM_TOKEN_TTL_SECONDS: int = 60 * 60 * 6 # 6 hours; supports long playback sessions

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./telegram_film.db"

@lru_cache()
def get_settings():
    return Settings()
