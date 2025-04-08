from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings."""
    APP_NAME: str = "SourceFinder API"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # Database settings
    DATABASE_URL: Optional[str] = None
    
    # API settings
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 