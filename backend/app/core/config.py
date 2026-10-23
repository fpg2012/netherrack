"""集中配置：全部来自环境变量，不在代码里写死密钥。"""
from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "flarum-api"
    debug: bool = False
    # dev | production：生产环境会在启动时校验下面几项
    env: str = "dev"

    database_url: str = "postgresql+asyncpg://flarum:flarum@localhost:5432/flarum"

    # 没有默认值：缺失时直接启动失败，避免用弱密钥上线
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_ttl: int = 15 * 60
    refresh_token_ttl: int = 7 * 24 * 3600
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    # 部署在 nginx 后面时打开，限流才会按真实客户端 IP 计数
    trust_proxy: bool = False

    cors_origins: list[str] = ["http://localhost:5173"]

    assets_dir: Path = BASE_DIR.parent / "data" / "public" / "assets"
    legacy_dump: Path = BASE_DIR.parent / "data" / "flarum-2026-10-23.sql.gz"

    page_size: int = 20
    max_page_size: int = 100

    @model_validator(mode="after")
    def _production_checks(self) -> "Settings":
        if self.env != "production":
            return self
        problems = []
        if not self.cookie_secure:
            problems.append("COOKIE_SECURE 必须为 true")
        if any(host in origin for origin in self.cors_origins
               for host in ("localhost", "127.0.0.1")):
            problems.append("CORS_ORIGINS 还是本地地址")
        if self.jwt_secret.startswith("dev-only"):
            problems.append("JWT_SECRET 还是默认值")
        if problems:
            raise ValueError("生产环境配置不完整：" + "；".join(problems))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
