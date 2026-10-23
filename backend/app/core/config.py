"""集中配置。

优先级：环境变量 > backend/.env > backend/config.toml > 这里的默认值。
密钥只放 .env（或环境变量），config.toml 只存非敏感项。
"""
import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

BASE_DIR = Path(__file__).resolve().parents[2]
# 生产环境可以用 CONFIG_FILE 指到 /etc/... 下的配置
CONFIG_FILE = Path(os.environ.get("CONFIG_FILE", BASE_DIR / "config.toml"))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        toml_file=CONFIG_FILE,
        extra="ignore",
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

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # 越靠前优先级越高：显式参数 > 环境变量 > .env > config.toml
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            TomlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )

    @model_validator(mode="after")
    def _resolve_paths(self) -> "Settings":
        # 相对路径按 backend/ 解析，避免依赖启动时的工作目录
        for name in ("assets_dir", "legacy_dump"):
            path = getattr(self, name)
            if not path.is_absolute():
                setattr(self, name, (BASE_DIR / path).resolve())
        return self

    @model_validator(mode="after")
    def _production_checks(self) -> "Settings":
        if self.env != "production":
            return self
        problems = []
        if not self.cookie_secure:
            problems.append("cookie_secure 必须为 true（config.toml 或环境变量）")
        if any(host in origin for origin in self.cors_origins
               for host in ("localhost", "127.0.0.1")):
            problems.append("cors_origins 还是本地地址")
        if self.jwt_secret.startswith("dev-only"):
            problems.append("jwt_secret 还是默认值")
        if problems:
            raise ValueError("生产环境配置不完整：" + "；".join(problems))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
