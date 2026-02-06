"""
Configuration Management for AI Voice Detection API
Environment-based settings with validation
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Set, Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Settings
    app_name: str = "AI Voice Detection API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # Authentication
    api_keys: Set[str] = {"demo_key_12345"}
    
    # Audio Processing
    target_sample_rate: int = 22050
    min_audio_duration: float = 1.0
    max_audio_duration: float = 60.0
    max_file_size_mb: int = 10
    
    # Model Settings
    model_path: str = "models"
    model_version: str = "1.0.0"
    
    # Redis Settings (for caching)
    redis_url: Optional[str] = None
    cache_ttl: int = 3600  # 1 hour
    
    # Database Settings
    database_url: Optional[str] = None
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    
    # Logging
    log_level: str = "INFO"
    
    # Monitoring
    enable_metrics: bool = True
    sentry_dsn: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Singleton instance
settings = get_settings()
