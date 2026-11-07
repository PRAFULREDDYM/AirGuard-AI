import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="allow"
    )

    PROJECT_NAME: str = "AirGuard AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    ENABLE_MOCK_PROVIDERS: bool = True

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"
    
    # Database: Default to sqlite+aiosqlite for local/sandboxed zero-friction execution
    # and support postgresql+asyncpg://user:pass@host:port/dbname for production
    DATABASE_URL: str = "sqlite+aiosqlite:///./airguard.db"
    
    # Security
    SECRET_KEY: str = "airguard-ai-dev-secret-key-change-in-production-1234567890"
    ENCRYPTION_KEY: str = "airguard-aes256-default-key-32b!"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    # Sensor thresholds & defaults
    STALE_SENSOR_TIMEOUT_SECONDS: int = 300  # 5 minutes
    DEFAULT_PURIFIER_COOLDOWN_SECONDS: int = 1800  # 30 mins

settings = Settings()

