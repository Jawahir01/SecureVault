from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List, Optional
import os
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    api_title: str = "SecureVault"
    api_version: str = "1.0.0"
    api_description: str = "A secure secrets management API"

    # Database
    database_url: str
    database_echo: bool = debug

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    encryption_key: str  # For AES-256 encryption

    # API
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 5
    rate_limit_period: int = 60  # seconds

    # Sentry (optional error tracking)
    sentry_dsn: Optional[str] = None

    # Logging
    log_level: str = "INFO"

    model_config = ConfigDict(env_file=".env", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    """Get settings instance (cached)."""
    return Settings()
