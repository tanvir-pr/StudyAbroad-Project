from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "StudyPath EU"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False

    database_url: str = Field(
        ...,
        description="Async SQLAlchemy URL, e.g. postgresql+asyncpg://user:pass@localhost:5432/studypath",
    )

    jwt_secret: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    # Required so the app fails fast if AI keys are missing at deploy time.
    # Day-1 routes do not call the LLM yet.
    openai_api_key: str = Field(..., min_length=1)
    openai_base_url: str = "https://api.openai.com/v1"
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    cors_origins: str = "http://localhost:3000"

    # Match engine weights (must sum to 1.0; IELTS weight redistributed if skipped)
    match_weight_cgpa: float = 0.35
    match_weight_ielts: float = 0.25
    match_weight_budget: float = 0.25
    match_weight_deadline: float = 0.15
    match_safe_threshold: float = 75.0
    match_target_threshold: float = 50.0
    match_deadline_full_days: int = 30
    match_cgpa_full_margin: float = 0.5

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
