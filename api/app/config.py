# app/config.py
# Centralizes all configuration in one place, loaded from environment
# variables (via the .env file). This means nothing sensitive (like
# DATABASE_URL or the agent token) is hardcoded in the actual code.
#pip install "uvicorn[standard]"

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    agent_shared_token: str
    redis_url: str = "redis://localhost:6379"
    discord_webhook_url: str

    class Config:
        env_file = ".env"

# A single shared instance imported wherever config is needed,
# instead of re-reading environment variables in multiple places.
settings = Settings()

