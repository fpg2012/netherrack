"""站点默认板块（config.toml 的 default_tag）通过 /meta 下发。"""
from app.core.config import settings
from app.models import Tag


async def make_tag(session, name: str, slug: str) -> Tag:
    tag = Tag(name=name, slug=slug)
    session.add(tag)
    await session.commit()
    return tag


async def test_meta_reports_configured_default_tag(session, client, monkeypatch) -> None:
    await make_tag(session, "茶话", "meta_tea")
    monkeypatch.setattr(settings, "default_tag", "meta_tea")

    body = (await client.get("/api/v1/meta")).json()
    assert body["default_tag"] == "meta_tea"


async def test_meta_ignores_unknown_default_tag(session, client, monkeypatch) -> None:
    # 配了一个不存在的标签：当没配处理，前端回落到「全部讨论」
    monkeypatch.setattr(settings, "default_tag", "meta_missing")

    body = (await client.get("/api/v1/meta")).json()
    assert body["default_tag"] is None


async def test_meta_without_default_tag(session, client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "default_tag", "")

    body = (await client.get("/api/v1/meta")).json()
    assert body["default_tag"] is None


async def test_meta_only_exposes_slug(session, client, monkeypatch) -> None:
    """只下发标签 slug，别把整份配置或标签表漏出去。"""
    await make_tag(session, "大小写", "meta_case")
    monkeypatch.setattr(settings, "default_tag", "meta_case")

    body = (await client.get("/api/v1/meta")).json()
    assert set(body) == {"discussions", "posts", "users", "untagged", "timezone", "default_tag"}
