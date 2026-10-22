"""集中配置：全部来自环境变量，不在代码里写死密钥。"""
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "flarum-api"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://flarum:flarum@localhost:5432/flarum"

    jwt_secret: str = Field(default="dev-only-secret-please-change", min_length=16)
    jwt_algorithm: str = "HS256"
    access_token_ttl: int = 15 * 60
    refresh_token_ttl: int = 7 * 24 * 3600
    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    cors_origins: list[str] = ["http://localhost:5173"]

    assets_dir: Path = BASE_DIR.parent / "data" / "public" / "assets"
    legacy_dump: Path = BASE_DIR.parent / "data" / "flarum-2026-10-23.sql.gz"

    page_size: int = 20
    max_page_size: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
