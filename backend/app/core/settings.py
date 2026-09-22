"""所有可修改参数集中在这里；环境变量 > backend/.env > 默认值。"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")
    app_env: Literal["development", "production"] = "development"
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'app.db').as_posix()}"
    data_dir: Path = BACKEND_DIR / ".data"
    jwt_secret: str = ""
    jwt_minutes: int = Field(default=120, ge=5, le=1440)
    admin_email: str = ""
    admin_password: str = ""
    llm_mode: Literal["demo", "compatible"] = "demo"
    llm_base_url: str = "http://127.0.0.1:11434/v1"
    llm_api_key: str = ""
    llm_model: str = "qwen3:8b"
    llm_timeout: float = Field(default=60, ge=1, le=300)
    model_trust_env: bool = False  # 本地模型默认直连；确需系统代理时显式开启
    llm_max_tokens: int = Field(default=1024, ge=64, le=8192)
    embedding_mode: Literal["demo", "compatible"] = "demo"
    embedding_base_url: str = "http://127.0.0.1:11434/v1"
    embedding_api_key: str = ""
    embedding_model: str = "nomic-embed-text"
    embedding_dimension: int = Field(default=256, ge=8, le=8192)
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_path: str = ""
    redis_url: str = ""
    rerank_model: str = ""  # 本地 CrossEncoder 路径；为空则只使用 RRF
    chunk_size: int = Field(default=700, ge=100, le=2000)
    chunk_overlap: int = Field(default=100, ge=0)
    max_upload_bytes: int = 5 * 1024 * 1024
    max_document_chars: int = 150_000
    agent_max_iterations: int = Field(default=5, ge=1, le=10)
    agent_timeout: float = Field(default=90, ge=5, le=300)
    mcp_api_url: str = "http://127.0.0.1:8000"

    @model_validator(mode="after")
    def validate_configuration(self):
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP 必须小于 CHUNK_SIZE")
        if self.app_env == "production" and len(self.jwt_secret) < 32:
            raise ValueError("生产环境必须设置至少 32 字符的 JWT_SECRET")
        if self.admin_password and len(self.admin_password) < 12:
            raise ValueError("ADMIN_PASSWORD 至少 12 字符")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
