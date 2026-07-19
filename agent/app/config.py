# app/config.py
# Loads agent configuration from environment variables (.env file).
# Mirrors the pattern used in the API's config.py, for consistency.

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_url: str
    agent_shared_token: str
    host_name: str
    report_interval_seconds: int = 10
    redis_url: str = "redis://localhost:6379" 

    class Config:
        env_file = ".env"

settings = Settings()