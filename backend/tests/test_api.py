from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from app.core.security import create_token
from app.models import AuditLog, Discussion, Notification, Post, User

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
