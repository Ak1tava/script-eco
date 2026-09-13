from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, supplied via environment variables."""

    database_url: str = "postgresql+psycopg2://ecology:ecology_local_password@localhost:5432/ecology"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    project_name: str = "EcoWatch Karaganda"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

