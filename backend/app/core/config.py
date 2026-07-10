from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_env_dir = Path(__file__).resolve().parents[2]  # backend/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_env_dir / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = f"sqlite+aiosqlite:///{_env_dir / 'whucs.db'}"
    REDIS_URL: str = "redis://localhost:6379/0"
    S3_ENDPOINT: str = "localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "whucs-files"
    S3_SECURE: bool = False
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    LLM_PROVIDER: str = ""
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""
    LLM_MODEL: str = "gpt-4.1-mini"
    DEEPSEEK_API_KEY: str = ""
    OPENAI_API_KEY: str = ""


settings = Settings()
