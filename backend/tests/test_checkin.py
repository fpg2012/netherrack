from datetime import timedelta

from app.core.security import create_token
from app.models import CheckIn, User
from app.services.checkins import site_today

CSRF = "test-csrf-token"


def auth(client, user: User) -> dict[str, str]:
    client.cookies.set("access_token", create_token(str(user.id), "access", 900))
    client.cookies.set("csrf_token", CSRF)
    return {"X-CSRF-Token": CSRF}


async def make_user(session, name: str) -> User:
    user = User(username=name, email=f"{name}@example.com", password_hash="x")
    session.add(user)
    await session.commit()
    return user


async def test_checkin_requires_login(session, client) -> None:
    client.cookies.clear()
    assert (await client.get("/api/v1/checkin")).status_code == 401
    assert (await client.post("/api/v1/checkin")).status_code == 403


async def test_checkin_once_per_day_and_streak(session, client) -> None:
    user = await make_user(session, "checkin_user")
    headers = auth(client, user)

    status = (await client.get("/api/v1/checkin")).json()
    assert status == {"checked_in_today": False, "current_streak": 0, "total_days": 0}

    today = site_today()
    session.add_all([
        CheckIn(user_id=user.id, checked_on=today - timedelta(days=1)),
        CheckIn(user_id=user.id, checked_on=today - timedelta(days=2)),
    ])
    await session.commit()

    # 今天没签，但昨天签过，连续天数仍然保留
    status = (await client.get("/api/v1/checkin")).json()
    assert status == {"checked_in_today": False, "current_streak": 2, "total_days": 2}

    res = await client.post("/api/v1/checkin", headers=headers)
    assert res.status_code == 200, res.text
    assert res.json() == {"checked_in_today": True, "current_streak": 3, "total_days": 3}

    # 同一天不能重复签
    assert (await client.post("/api/v1/checkin", headers=headers)).status_code == 409
    assert (await client.get("/api/v1/checkin")).json()["total_days"] == 3


async def test_broken_streak(session, client) -> None:
    user = await make_user(session, "checkin_broken")
    auth(client, user)
    today = site_today()
    session.add(CheckIn(user_id=user.id, checked_on=today - timedelta(days=2)))
    await session.commit()

    status = (await client.get("/api/v1/checkin")).json()
    assert status["checked_in_today"] is False
    assert status["current_streak"] == 0
    assert status["total_days"] == 1
