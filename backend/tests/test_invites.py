from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.security import create_token
from app.models import AuditLog, Invite, User

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


def register_body(code: str, name: str, password: str = "correct horse battery") -> dict:
    return {"code": code, "username": name, "email": f"{name}@example.com",
            "password": password, "nickname": "新用户"}


async def create_invite(client, headers: dict, **payload) -> dict:
    res = await client.post("/api/v1/invites", json={"expires_in_days": 7, **payload},
                            headers=headers)
    assert res.status_code == 201, res.text
    return res.json()


async def test_only_admin_can_manage_invites(session, client) -> None:
    user = await make_user(session, "invite_plain")
    headers = auth(client, user)
    assert (await client.post("/api/v1/invites", json={}, headers=headers)).status_code == 403
    assert (await client.get("/api/v1/invites")).status_code == 403

    guest(client)
    # 未登录且没带 CSRF，先被 CSRF 挡下（403）
    assert (await client.post("/api/v1/invites", json={})).status_code == 403
    assert (await client.get("/api/v1/invites")).status_code == 401


async def test_invite_register_and_reuse(session, client) -> None:
    admin = await make_user(session, "invite_admin", admin=True)
    headers = auth(client, admin)
    created = await create_invite(client, headers, note="给朋友")
    code = created["code"]
    assert len(code) == 23 and code.count("-") == 3

    listing = (await client.get("/api/v1/invites")).json()
    assert listing[0]["status"] == "active"
    # 列表不能回显明文或哈希
    assert "code" not in listing[0] and "code_hash" not in listing[0]

    guest(client)
    res = await client.post("/api/v1/auth/register", json=register_body(code, "invite_new"))
    assert res.status_code == 201, res.text
    assert res.json()["user"]["username"] == "invite_new"
    assert "access_token" in client.cookies

    # 同一个码不能再用
    guest(client)
    again = await client.post("/api/v1/auth/register", json=register_body(code, "invite_other"))
    assert again.status_code == 400

    invite = await session.scalar(select(Invite).where(Invite.id == created["id"]))
    assert invite.used_at is not None and invite.used_by is not None

    # 审计里有注册和发码，且没有明文
    actions = {row.action for row in (await session.scalars(select(AuditLog))).all()}
    assert {"invite.create", "user.register"} <= actions


async def test_register_rejects_invalid_invites(session, client) -> None:
    admin = await make_user(session, "invite_admin2", admin=True)
    headers = auth(client, admin)

    revoked = await create_invite(client, headers)
    assert (await client.delete(f"/api/v1/invites/{revoked['id']}",
                                headers=headers)).status_code == 204
    guest(client)
    res = await client.post("/api/v1/auth/register",
                            json=register_body(revoked["code"], "invite_r1"))
    assert res.status_code == 400

    headers = auth(client, admin)
    expired = await create_invite(client, headers)
    row = await session.scalar(select(Invite).where(Invite.id == expired["id"]))
    row.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    await session.commit()
    guest(client)
    res = await client.post("/api/v1/auth/register",
                            json=register_body(expired["code"], "invite_r2"))
    assert res.status_code == 400

    res = await client.post("/api/v1/auth/register",
                            json=register_body("AAAA-BBBB-CCCC-DDDD", "invite_r3"))
    assert res.status_code == 400


async def test_register_validation(session, client) -> None:
    admin = await make_user(session, "invite_admin3", admin=True)
    headers = auth(client, admin)
    created = await create_invite(client, headers)

    guest(client)
    # 密码太短
    res = await client.post("/api/v1/auth/register",
                            json=register_body(created["code"], "invite_v1", password="short"))
    assert res.status_code == 422

    # 用户名已被占用（大小写不敏感）
    existing = await make_user(session, "invite_taken")
    res = await client.post("/api/v1/auth/register",
                            json=register_body(created["code"], existing.username.upper()))
    assert res.status_code == 409

    # 邮箱重复
    body = register_body(created["code"], "invite_v2")
    body["email"] = existing.email
    res = await client.post("/api/v1/auth/register", json=body)
    assert res.status_code == 409
