from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select

from app.core.security import create_token, hash_password, verify_password
from app.models import AuditLog, Discussion, Notification, Post, RefreshToken, User

CSRF = "test-csrf-token"


def auth(client, user: User) -> dict[str, str]:
    client.cookies.set("access_token", create_token(str(user.id), "access", 900))
    client.cookies.set("csrf_token", CSRF)
    return {"X-CSRF-Token": CSRF}


def guest(client) -> None:
    client.cookies.clear()


async def make_user(session, name: str, admin: bool = False) -> User:
    user = User(username=name, email=f"{name}@example.com", password_hash="x",
                is_admin=admin)
    session.add(user)
    await session.commit()
    return user


async def make_discussion(session, author: User, *, public: bool = False,
                          title: str = "t") -> Discussion:
    now = datetime.now(UTC)
    discussion = Discussion(title=title, author_id=author.id, created_at=now,
                            last_posted_at=now, post_count=1, is_public=public)
    session.add(discussion)
    await session.commit()
    await session.refresh(discussion)
    post = Post(discussion_id=discussion.id, number=1, author_id=author.id,
                body_html="<p>op</p>", created_at=now)
    session.add(post)
    await session.commit()
    return discussion


async def make_post(session, discussion: Discussion, author: User, number: int) -> Post:
    post = Post(discussion_id=discussion.id, number=number, author_id=author.id,
                body_html=f"<p>post {number}</p>", created_at=datetime.now(UTC))
    session.add(post)
    await session.commit()
    return post


async def test_guest_only_sees_public(session, client) -> None:
    author = await make_user(session, "api_author1")
    private = await make_discussion(session, author, title="private one")
    public = await make_discussion(session, author, public=True, title="public one")

    guest(client)
    listing = (await client.get("/api/v1/discussions?per_page=100")).json()
    ids = {item["id"] for item in listing["items"]}
    assert public.id in ids
    assert private.id not in ids
    assert (await client.get(f"/api/v1/discussions/{private.id}")).status_code == 404

    auth(client, author)
    assert (await client.get(f"/api/v1/discussions/{private.id}")).status_code == 200


async def test_search_requires_login(session, client) -> None:
    guest(client)
    assert (await client.get("/api/v1/search?q=x")).status_code == 401
    user = await make_user(session, "api_author2")
    auth(client, user)
    assert (await client.get("/api/v1/search?q=x")).status_code == 200


async def test_edit_permissions(session, client) -> None:
    author = await make_user(session, "api_author3")
    other = await make_user(session, "api_other3")
    discussion = await make_discussion(session, author, public=True)
    post = (await session.scalars(
        select(Post).where(Post.discussion_id == discussion.id))).first()

    headers = auth(client, other)
    response = await client.patch(f"/api/v1/posts/{post.id}", headers=headers,
                                  json={"body_md": "hack"})
    assert response.status_code == 403

    headers = auth(client, author)
    response = await client.patch(f"/api/v1/posts/{post.id}", headers=headers,
                                  json={"body_md": "edited"})
    assert response.status_code == 200

    post.is_legacy = True
    await session.commit()
    response = await client.patch(f"/api/v1/posts/{post.id}", headers=headers,
                                  json={"body_md": "again"})
    assert response.status_code == 409


async def test_publish_and_collapse(session, client) -> None:
    author = await make_user(session, "api_author4")
    other = await make_user(session, "api_other4")
    admin = await make_user(session, "api_admin4", admin=True)
    discussion = await make_discussion(session, author)

    # 只有楼主和管理员能设公开
    headers = auth(client, other)
    assert (await client.patch(f"/api/v1/discussions/{discussion.id}",
                               headers=headers, json={"is_public": True})).status_code == 403
    headers = auth(client, author)
    assert (await client.patch(f"/api/v1/discussions/{discussion.id}",
                               headers=headers, json={"is_public": True})).status_code == 200

    # 管理员折叠：强制不公开、从列表消失、游客看不到
    headers = auth(client, admin)
    body = (await client.patch(f"/api/v1/discussions/{discussion.id}",
                               headers=headers, json={"is_collapsed": True})).json()
    assert body["is_collapsed"] is True and body["is_public"] is False
    guest(client)
    assert (await client.get(f"/api/v1/discussions/{discussion.id}")).status_code == 404

    # 折叠状态下不能再设公开
    headers = auth(client, author)
    assert (await client.patch(f"/api/v1/discussions/{discussion.id}",
                               headers=headers, json={"is_public": True})).status_code == 409


async def test_collapsed_post_body_hidden(session, client) -> None:
    author = await make_user(session, "api_author5")
    admin = await make_user(session, "api_admin5", admin=True)
    discussion = await make_discussion(session, author, public=True)
    post = await make_post(session, discussion, author, 2)

    headers = auth(client, admin)
    response = await client.patch(f"/api/v1/posts/{post.id}/collapse",
                                  headers=headers, json={"is_collapsed": True})
    assert response.json()["body_html"] == ""

    timeline = (await client.get(
        f"/api/v1/discussions/{discussion.id}/timeline?per_page=10")).json()
    item = next(i for i in timeline["items"] if i.get("post", {}).get("id") == post.id)
    assert item["post"]["is_collapsed"] is True
    assert item["post"]["body_html"] == ""


async def test_reply_to_notifies_floor_author(session, client) -> None:
    a = await make_user(session, "api_author6")
    b = await make_user(session, "api_floor6")
    c = await make_user(session, "api_replier6")
    discussion = await make_discussion(session, a)
    floor = await make_post(session, discussion, b, 2)

    headers = auth(client, c)
    response = await client.post(
        f"/api/v1/discussions/{discussion.id}/posts", headers=headers,
        json={"body_md": "reply", "reply_to_post_id": floor.id},
    )
    assert response.status_code == 201

    rows = (await session.scalars(
        select(Notification).where(Notification.recipient_id == b.id))).all()
    assert any(n.kind == "reply" for n in rows)


async def test_mention_scope_limits_targets(session, client) -> None:
    a = await make_user(session, "api_author7")
    b = await make_user(session, "api_floor7")
    outsider = await make_user(session, "api_outsider7")
    discussion = await make_discussion(session, a)
    await make_post(session, discussion, b, 2)

    headers = auth(client, b)
    response = await client.post(
        f"/api/v1/discussions/{discussion.id}/posts", headers=headers,
        json={"body_md": "@api_author7 @api_outsider7"},
    )
    html = response.json()["body_html"]
    assert f'href="/u/{a.id}"' in html
    assert f'href="/u/{outsider.id}"' not in html


async def test_notification_mark_read(session, client) -> None:
    user = await make_user(session, "api_notify8")
    discussion = await make_discussion(session, user)
    note = Notification(recipient_id=user.id, actor_id=user.id, kind="system",
                        discussion_id=discussion.id, title="t", body="b")
    session.add(note)
    await session.commit()

    headers = auth(client, user)
    assert (await client.get("/api/v1/notifications/unread")).json()["count"] >= 1
    assert (await client.post(f"/api/v1/notifications/{note.id}/read",
                              headers=headers)).status_code == 204
    assert (await client.get("/api/v1/notifications/unread")).json()["count"] == 0


async def test_audit_log_written(session, client) -> None:
    author = await make_user(session, "api_author9")
    admin = await make_user(session, "api_admin9", admin=True)
    discussion = await make_discussion(session, author, public=True)

    headers = auth(client, admin)
    await client.patch(f"/api/v1/discussions/{discussion.id}", headers=headers,
                       json={"is_collapsed": True})
    rows = (await session.scalars(
        select(AuditLog).where(AuditLog.action == "discussion.collapse"))).all()
    assert len(rows) == 1
    assert rows[0].target_id == discussion.id


@pytest.mark.parametrize("path", ["/api/v1/discussions", "/api/v1/tags", "/healthz"])
async def test_security_headers_present(client, path) -> None:
    response = await client.get(path)
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-content-type-options"] == "nosniff"


async def test_admin_resets_user_password(session, client) -> None:
    target = await make_user(session, "api_reset11")
    admin = await make_user(session, "api_admin11", admin=True)
    session.add(RefreshToken(
        user_id=target.id, token_hash="r" * 64,
        expires_at=datetime.now(UTC),
    ))
    await session.commit()

    # 普通用户不能重置别人
    headers = auth(client, target)
    response = await client.post(
        f"/api/v1/users/{target.id}/reset-password", headers=headers, json={})
    assert response.status_code == 403

    # 管理员可以指定新密码，并清掉该用户的 refresh token
    headers = auth(client, admin)
    response = await client.post(
        f"/api/v1/users/{target.id}/reset-password", headers=headers,
        json={"new_password": "newpass123"},
    )
    assert response.status_code == 200
    assert response.json()["password"] == "newpass123"
    await session.refresh(target)
    assert verify_password("newpass123", target.password_hash)[0] is True
    tokens = await session.scalar(
        select(func.count()).select_from(RefreshToken)
        .where(RefreshToken.user_id == target.id))
    assert tokens == 0
    log = await session.scalar(
        select(AuditLog).where(AuditLog.action == "user.password_reset"))
    assert log is not None and log.payload["generated"] is False

    # 不传密码时自动生成
    response = await client.post(
        f"/api/v1/users/{target.id}/reset-password", headers=headers, json={})
    assert response.status_code == 200
    password = response.json()["password"]
    assert len(password) >= 8
    await session.refresh(target)
    assert verify_password(password, target.password_hash)[0] is True


async def test_admin_ban_blocks_login(session, client) -> None:
    target = User(username="api_ban12", email="api_ban12@example.com",
                  password_hash=hash_password("password123"))
    admin = await make_user(session, "api_admin12", admin=True)
    session.add(target)
    await session.commit()

    # 正常可以登录
    guest(client)
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "api_ban12", "password": "password123"},
    )
    assert response.status_code == 200

    # 普通用户不能封禁别人
    headers = auth(client, target)
    response = await client.patch(
        f"/api/v1/users/{target.id}/status", headers=headers, json={"is_active": False})
    assert response.status_code == 403

    # 管理员封禁：refresh token 被清空，已有 access token 也立即失效
    headers = auth(client, admin)
    response = await client.patch(
        f"/api/v1/users/{target.id}/status", headers=headers, json={"is_active": False})
    assert response.status_code == 204
    tokens = await session.scalar(
        select(func.count()).select_from(RefreshToken)
        .where(RefreshToken.user_id == target.id))
    assert tokens == 0
    auth(client, target)
    assert (await client.get("/api/v1/auth/me")).status_code == 401

    # 被封禁后不能登录
    guest(client)
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "api_ban12", "password": "password123"},
    )
    assert response.status_code == 401

    # 解封后恢复登录
    headers = auth(client, admin)
    response = await client.patch(
        f"/api/v1/users/{target.id}/status", headers=headers, json={"is_active": True})
    assert response.status_code == 204
    guest(client)
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "api_ban12", "password": "password123"},
    )
    assert response.status_code == 200
