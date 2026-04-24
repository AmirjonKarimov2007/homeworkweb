from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_ENV: str = "development"
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000"

    DATABASE_URL: str = Field(
        "postgresql+asyncpg://postgres:12345678@localhost:5432/homeworkweb",
        description="Async database URL",
    )
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # Defaults are dev-safe placeholders; override in .env for production
    JWT_SECRET: str = "CHANGE_ME_STRONG_SECRET"
    JWT_REFRESH_SECRET: str = "CHANGE_ME_STRONG_REFRESH_SECRET"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    ALLOW_LATE_SUBMISSION: bool = True
    MAX_REVISION_ATTEMPTS: int = 2

    SCHEDULER_TIMEZONE: str = "Asia/Tashkent"
    REMINDER_24H_ENABLED: bool = True
    REMINDER_3H_ENABLED: bool = True

    BROADCAST_THROTTLE_MS: int = 100
    BROADCAST_RETRY_ATTEMPTS: int = 3
    BROADCAST_RETRY_DELAY_MINUTES: int = 5

    LOG_LEVEL: str = "INFO"

    REDIS_URL: str | None = None

    BOT_INTERNAL_TOKEN: str = "CHANGE_ME_INTERNAL_BOT_TOKEN"

    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    INIT_DB_ON_STARTUP: bool = True
    RATE_LIMIT_ENABLED: bool = False

    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
