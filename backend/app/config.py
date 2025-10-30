"""Application configuration management.

This module uses pydantic-settings to load configuration from environment
variables, providing type safety and validation for all settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings have sensible defaults for development, but should be
    overridden in production via environment variables or .env file.
    """

    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    redis_stream_name: str = "pdf-jobs"
    redis_consumer_group: str = "pdf-workers"
    redis_consumer_name: str = "worker-1"
    redis_result_ttl_seconds: int = 3600  # 1 hour

    # API Keys
    google_api_key: str = ""
    mistral_api_key: str = ""

    # File Upload Configuration
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 25
    allowed_extensions: list[str] = [".pdf"]

    # CORS Configuration (for frontend)
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5173",  # Vite default
        "https://pdf-processor-navp1zrg3-alejandro-changs-projects-029b7b9c.vercel.app",  # Production frontend
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def validate_api_keys(self) -> dict[str, bool]:
        """Check which API keys are configured.

        Returns:
            Dictionary with parser names and their API key availability status.
        """
        return {
            "gemini": bool(self.google_api_key),
            "mistral": bool(self.mistral_api_key),
        }

    def get_max_file_size_bytes(self) -> int:
        """Get maximum file size in bytes.

        Returns:
            Maximum file size in bytes.
        """
        return self.max_file_size_mb * 1024 * 1024

    def ensure_upload_dir(self) -> None:
        """Create upload directory if it doesn't exist.

        This should be called on application startup to ensure
        the upload directory is available.
        """
        os.makedirs(self.upload_dir, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    This function uses lru_cache to ensure settings are loaded only once
    and reused across the application, improving performance and ensuring
    consistency.

    Returns:
        Singleton Settings instance.
    """
    return Settings()
