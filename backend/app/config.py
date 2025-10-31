"""Application configuration management.

This module provides a centralized configuration system using Pydantic Settings.
All environment variables are loaded and validated here, making it easy to
manage configuration across different environments (development, staging, production).

Environment variables can be set in:
1. System environment variables
2. .env file in the project root
3. Docker/cloud platform environment configurations
"""

import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.
    
    This class defines all configuration parameters for the application.
    Values are automatically loaded from environment variables or .env file.
    
    Attributes:
        app_name: Name of the application.
        app_version: Version of the application.
        google_api_key: API key for Google Gemini.
        mistral_api_key: API key for Mistral AI.
        upload_dir: Directory for storing uploaded files.
        max_file_size_mb: Maximum allowed file size in megabytes.
        allowed_extensions: List of allowed file extensions.
        redis_url: URL for Redis connection.
        redis_stream_name: Name of the Redis stream for job queue.
        redis_consumer_group: Name of the Redis consumer group.
        redis_consumer_name: Name of this Redis consumer.
        redis_result_ttl_seconds: TTL for job results in Redis.
        cors_origins: List of allowed CORS origins for frontend access.
    """
    
    # Application metadata
    app_name: str = "PDF Processor"
    app_version: str = "0.1.0"
    
    # API Keys - Required for PDF processing
    google_api_key: str = Field(
        default="",
        description="Google API key for Gemini LLM"
    )
    mistral_api_key: str = Field(
        default="",
        description="Mistral API key for Mistral LLM"
    )
    
    # File Upload Configuration
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 25
    allowed_extensions: list[str] = [".pdf"]
    
    # Redis Configuration (for job queue)
    redis_url: str = "redis://localhost:6379"
    redis_stream_name: str = "pdf-jobs"
    redis_consumer_group: str = "pdf-workers"
    redis_consumer_name: str = "worker-1"
    redis_result_ttl_seconds: int = 3600
    
    # CORS Configuration (for frontend)
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5173",  # Vite default
        "https://pdf-processor-1tbl1hc01-alejandro-changs-projects-029b7b9c.vercel.app",  # Production frontend
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
