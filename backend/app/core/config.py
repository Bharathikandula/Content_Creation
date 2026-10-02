from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "Fashion Creator Agent"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fashion_creator"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/fashion_creator"

    # Gemini API
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_STRONG: str = "gemini-3.5-flash"
    GEMINI_MODEL_CHEAP: str = "gemini-3.5-flash-lite"

    # SerpAPI
    SERPAPI_API_KEY: str = ""

    # Cuelinks
    CUELINKS_API_KEY: str = ""
    CUELINKS_SUBID: str = "fashion_creator"

    # S3 Storage
    S3_ENDPOINT_URL: Optional[str] = None
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET_NAME: str = "fashion-creator-photos"
    S3_REGION: str = "us-east-1"

    # Photo expiry (24 hours)
    PHOTO_EXPIRY_HOURS: int = 24

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Supported languages
    SUPPORTED_LANGUAGES: list = ["en", "hi", "te", "ta", "ml"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()