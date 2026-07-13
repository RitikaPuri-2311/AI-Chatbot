import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_TTL: int = int(os.getenv("REDIS_TTL", "86400"))
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    JIRA_BASE_URL: str = os.getenv("JIRA_BASE_URL", "")
    JIRA_EMAIL: str = os.getenv("JIRA_EMAIL", "")
    JIRA_API_TOKEN: str = os.getenv("JIRA_API_TOKEN", "")
    JIRA_PROJECT_KEY: str = os.getenv("JIRA_PROJECT_KEY", "")

settings = Settings()