"""
JobPilot — Application Configuration
Uses Pydantic BaseSettings for type-safe environment variable management.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- General ---
    PROJECT_NAME: str = "JobPilot"
    ENVIRONMENT: str = "development"

    # --- Database ---
    MONGODB_URL: str = "mongodb+srv://mohdalipatel8976_db_user:fdfT2yrrno8emtUi@cluster0.g0xoydr.mongodb.net/?appName=Cluster0"
    MONGODB_DB_NAME: str = "jobpilot"

    # --- Redis ---
    REDIS_URL: str = "redis://redis:6379/0"

    # --- JWT Authentication ---
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- CORS ---
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    # --- AI (Gemini) ---
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # --- Telegram ---
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""

    # --- Gmail ---
    GMAIL_CLIENT_ID: str = ""
    GMAIL_CLIENT_SECRET: str = ""
    GMAIL_REFRESH_TOKEN: str = ""
    GMAIL_USER_EMAIL: str = ""
    EMAIL_CHECK_INTERVAL_SECONDS: int = 300

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


# Singleton instance
settings = Settings()
