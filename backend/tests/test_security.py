from starlette.requests import Request

from app.core.config import Settings
from app.core.headers import security_headers
from app.core.ratelimit import client_ip


def _request(headers: dict[str, str]) -> Request:
    raw = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    return Request({"type": "http", "headers": raw, "client": ("127.0.0.1", 1234),
                    "scheme": "http", "method": "GET", "path": "/"})


def test_client_ip_ignores_forwarded_by_default() -> None:
    req = _request({"x-forwarded-for": "203.0.113.9, 10.0.0.1"})
    assert client_ip(req) == "127.0.0.1"


def test_client_ip_uses_first_forwarded_entry(monkeypatch) -> None:
    from app.core import ratelimit

    monkeypatch.setattr(ratelimit.settings, "trust_proxy", True)
    req = _request({"x-forwarded-for": "203.0.113.9, 10.0.0.1"})
    assert client_ip(req) == "203.0.113.9"


def test_security_headers() -> None:
    headers = security_headers("/api/v1/discussions", True)
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert "Strict-Transport-Security" in headers
    # 文档页需要加载 CDN，不放 CSP
    assert "Content-Security-Policy" not in security_headers("/api/docs", False)


def test_production_rejects_insecure_settings() -> None:
    import pytest
    from pydantic import ValidationError

    base = dict(_env_file=None, jwt_secret="x" * 40, env="production",
                cors_origins=["https://forum.example.com"], cookie_secure=True)
    with pytest.raises(ValidationError):          # 没开 secure cookie
        Settings(**{**base, "cookie_secure": False})
    with pytest.raises(ValidationError):          # CORS 还是本地地址
        Settings(**{**base, "cors_origins": ["http://localhost:5173"]})
    # 合规配置可以启动
    assert Settings(**base).cookie_secure is True


def test_toml_config_loaded() -> None:
    from app.core.config import Settings

    s = Settings(_env_file=None, jwt_secret="x" * 40)
    assert s.app_name == "soulsand"
    assert s.page_size == 20
    # 相对路径按 backend/ 解析成绝对路径
    assert s.assets_dir.is_absolute()
    assert s.assets_dir.parts[-3:] == ("data", "public", "assets")


def test_env_overrides_toml(monkeypatch) -> None:
    from app.core.config import Settings

    monkeypatch.setenv("PAGE_SIZE", "7")
    monkeypatch.setenv("APP_NAME", "from-env")
    s = Settings(_env_file=None, jwt_secret="x" * 40)
    assert s.page_size == 7
    assert s.app_name == "from-env"
