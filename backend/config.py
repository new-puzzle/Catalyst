from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Catalyst - AI Smart Journal"
    debug: bool = True

    # Database
    database_url: str = "sqlite:///./data/db/conversations.db"
    chroma_persist_dir: str = "./data/db/vector_store"

    # AI API Keys (set via environment variables)
    gemini_api_key: str = ""
    deepseek_api_key: str = ""
    anthropic_api_key: str = ""

    # Hume AI
    hume_api_key: str = ""

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""

    # Cost tracking (per 1M tokens)
    gemini_flash_cost: float = 0.075
    deepseek_cost: float = 0.14
    claude_cost: float = 3.00

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
