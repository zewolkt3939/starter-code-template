from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "AI20K Agent"
    app_env: Literal["development", "production", "test"] = "development"
    app_port: int = Field(default=8000, ge=1, le=65535)
    app_host: str = "0.0.0.0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    cors_origins: str = "http://localhost:3000"

    # LLM — cascade router: mỗi task type một model (bài học cost-management:
    # không đốt model mạnh cho việc classify). Judge PHẢI khác model generator
    # để tránh self-preference bias (bài học team 002 — eval judge riêng).
    openai_api_key: str = ""
    model_name: str = "gpt-4o"  # legacy alias cho model_generate
    model_classify: str = "gpt-4o-mini"  # cheap: classify / route / quyết định tool
    model_generate: str = "gpt-4o"  # strong: sinh câu trả lời cuối
    model_judge: str = "gpt-4o-mini"  # judge: khác model_generate mặc định
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)

    # Agent loop — escape hatch chống loop vô hạn (bài học team 011:
    # luôn phải có một đường tới END dù LLM cứ đòi gọi tool mãi)
    agent_max_iterations: int = Field(default=8, ge=1, le=50)

    # Database
    database_url: str = "sqlite:///./data/app.db"

    # Vector Store
    chroma_persist_dir: str = "./data/chroma"


@lru_cache
def get_settings() -> Settings:
    return Settings()
