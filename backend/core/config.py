from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True,
    )

    PROJECT_NAME: str = "Telegram Film"
    API_V1_STR: str = "/api"

    # Telegram
    BOT_TOKEN: str = ""
    API_ID: int = 0
    API_HASH: str = ""
    STORAGE_CHANNEL_ID: str = ""
    WEBAPP_URL: str = ""
    ALLOWED_TELEGRAM_IDS: str = ""
    ADMIN_TELEGRAM_IDS: str = ""

    # Filesystem / upload
    UPLOAD_ROOTS: str = ""
    UPLOAD_SPEED_LIMIT_MB: float = 0.0

    # Authentication / playback
    SECRET_KEY: str = ""
    SESSION_COOKIE_NAME: str = "telefilm_session"
    SESSION_TTL_SECONDS: int = 60 * 60 * 12
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_PARTITIONED: bool = True
    STREAM_TOKEN_TTL_SECONDS: int = 60 * 60 * 6
    STREAM_TOKEN_RATE_PER_MINUTE: int = 30
    STREAM_REQUEST_RATE_PER_MINUTE: int = 300
    MAX_CONCURRENT_STREAMS_PER_USER: int = 6

    # App exposure
    ENABLE_API_DOCS: bool = False

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./telegram_film.db"


@lru_cache()
def get_settings():
    return Settings()
