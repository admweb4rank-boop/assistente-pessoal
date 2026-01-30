"""
TB Personal OS - Configuration
Centralized settings using Pydantic
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "TB Personal OS"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_SECRET_KEY: str
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # Google APIs
    GOOGLE_API_KEY: str = ""
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    GOOGLE_SCOPES: str
    
    # Gemini AI
    GEMINI_API_KEY: str
    GEMINI_API_KEY_2: str = ""  # Segunda chave para fallback automático
    GEMINI_MODEL: str = "gemini-pro"
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBHOOK_URL: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:5174"
    
    # User
    OWNER_USER_ID: str = ""
    OWNER_TELEGRAM_CHAT_ID: str = ""
    OWNER_TIMEZONE: str = "America/Sao_Paulo"
    
    # Features
    FEATURE_ML_ENABLED: bool = False
    FEATURE_AUTO_EXECUTE: bool = False
    FEATURE_VOICE_INPUT: bool = False
    
    # OpenAI (Whisper)
    OPENAI_API_KEY: str = ""
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def google_scopes_list(self) -> List[str]:
        """Convert comma-separated scopes to list"""
        base_scopes = {
            'calendar': 'https://www.googleapis.com/auth/calendar',
            'gmail': 'https://www.googleapis.com/auth/gmail.modify',
            'drive': 'https://www.googleapis.com/auth/drive',
            'sheets': 'https://www.googleapis.com/auth/spreadsheets',
        }
        requested = self.GOOGLE_SCOPES.split(',')
        return [base_scopes.get(s.strip(), s.strip()) for s in requested]


# Global settings instance
settings = Settings()
