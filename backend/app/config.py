from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/paytrack"  # pragma: allowlist secret

    # JWT
    jwt_secret_key: str = "your-super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours

    # App
    app_name: str = "PayTrack"
    debug: bool = True

    # Ollama LLM - Primary (Remote)
    ollama_base_url: str = "http://192.168.1.9:11434"
    ollama_model: str = "qwen3:30b"
    ollama_timeout: int = 180  # Longer for larger model

    # No local fallback - remote only
    ollama_fallback_enabled: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
