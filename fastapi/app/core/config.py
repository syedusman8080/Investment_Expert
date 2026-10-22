from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    app_name: str = "Finance Guru"
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    llm_model_path: str = "fastapi/models/Qwen3-4B-Q4_K_M.gguf"
    llm_cli_path: str = "fastapi/models/llama-b10833-bin-win-cuda-12.4-x64/llama-cli.exe"
    embedding_model_path: str = "fastapi/models/embedding"
    vector_db_path: str = "fastapi/data/chroma"
    document_storage_path: str = "fastapi/data/documents"
    llm_context_size: int = 4096
    llm_temperature: float = 0.2
    llm_max_tokens: int = 4096
    llm_gpu_layers: int = 0
    retrieval_top_k: int = 5
    chunk_size: int = 1200
    chunk_overlap: int = 200
    database_url: str = "sqlite:///./finance_guru.db"
    auth_secret: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7
    llm_provider: str = "local"
    llm_api_url: str = "https://api-inference.huggingface.co/v1/chat/completions"
    llm_api_key: str = ""
    llm_api_model: str = "Qwen/Qwen2.5-7B-Instruct"
    superadmin_email: str = ""
    superadmin_password: str = ""

    def resolve_path(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return Path(__file__).resolve().parents[3] / path

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
