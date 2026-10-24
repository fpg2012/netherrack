"""时间线里的操作记录：写入的 payload 格式、文案，以及分页时归属哪一页。"""
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.security import create_token
from app.models import Discussion, DiscussionEvent, Post, Tag, User

CSRF = "test-csrf-token"


def auth(client, user: User) -> dict[str, str]:
    client.cookies.set("access_token", create_token(str(user.id), "access", 900))
    client.cookies.set("csrf_token", CSRF)
    return {"X-CSRF-Token": CSRF}


async def make_user(session, name: str, admin: bool = False) -> User:
    user = User(username=name, email=f"{name}@example.com", password_hash="x", is_admin=admin)
    session.add(user)
    await session.commit()
    return user


async def make_discussion(session, author: User, *, started: datetime) -> Discussion:
    discussion = Discussion(title="t", author_id=author.id, created_at=started,
                            last_posted_at=started, post_count=1, is_public=True)
    session.add(discussion)
    await session.commit()
    await session.refresh(discussion)
    session.add(Post(discussion_id=discussion.id, number=1, author_id=author.id,
                     body_html="<p>op</p>", created_at=started))
    await session.commit()
    return discussion


async def make_post(session, discussion: Discussion, author: User, number: int,
                    created_at: datetime) -> Post:
    post = Post(discussion_id=discussion.id, number=number, author_id=author.id,
                body_html=f"<p>post {number}</p>", created_at=created_at)
    session.add(post)
    await session.commit()
    return post


async def timeline(client, discussion: Discussion, page: int = 1) -> list[dict]:
    response = await client.get(
        f"/api/v1/discussions/{discussion.id}/timeline?per_page=20&page={page}"
    )
    assert response.status_code == 200
    return response.json()["items"]


def texts(items: list[dict]) -> list[str]:
    return [i["event"]["text"] for i in items if i["type"] == "event"]


async def test_rename_and_tag_text(session, client) -> None:
    admin = await make_user(session, "tl_admin1", admin=True)
    first = Tag(name="闲聊", slug="chat")
    second = Tag(name="提问", slug="ask")
    session.add_all([first, second])
    await session.commit()
    discussion = await make_discussion(session, admin,
                                       started=datetime.now(UTC) - timedelta(hours=2))

    headers = auth(client, admin)
    renamed = await client.patch(f"/api/v1/discussions/{discussion.id}", headers=headers,
                                 json={"title": "新标题"})
    assert renamed.status_code == 200
    tagged = await client.patch(f"/api/v1/discussions/{discussion.id}", headers=headers,
                                json={"tags": ["chat"]})
    assert tagged.status_code == 200
    retagged = await client.patch(f"/api/v1/discussions/{discussion.id}", headers=headers,
                                  json={"tags": ["ask"]})
    assert retagged.status_code == 200

    lines = texts(await timeline(client, discussion))
    assert "tl_admin1 将标题从「t」改为「新标题」" in lines
    assert "tl_admin1 添加标签 闲聊" in lines
    assert "tl_admin1 添加标签 提问，移除标签 闲聊" in lines


async def test_event_after_last_post_is_visible(session, client) -> None:
    """改标题发生在最后一条回复之后时，仍要出现在时间线上（曾经会被时间窗过滤掉）。"""
    admin = await make_user(session, "tl_admin2", admin=True)
    started = datetime.now(UTC) - timedelta(hours=3)
    discussion = await make_discussion(session, admin, started=started)
    await make_post(session, discussion, admin, 2, started + timedelta(minutes=1))

    headers = auth(client, admin)
    assert (await client.patch(f"/api/v1/discussions/{discussion.id}", headers=headers,
                               json={"title": "改名"})).status_code == 200

    assert "tl_admin2 将标题从「t」改为「改名」" in texts(await timeline(client, discussion))


async def test_post_collapse_and_visibility_recorded(session, client) -> None:
    admin = await make_user(session, "tl_admin3", admin=True)
    started = datetime.now(UTC) - timedelta(hours=3)
    discussion = await make_discussion(session, admin, started=started)
    post = await make_post(session, discussion, admin, 2, started + timedelta(minutes=1))

    headers = auth(client, admin)
    assert (await client.patch(f"/api/v1/posts/{post.id}/collapse", headers=headers,
                               json={"is_collapsed": True})).status_code == 200
    assert (await client.patch(f"/api/v1/discussions/{discussion.id}", headers=headers,
                               json={"is_public": False})).status_code == 200
    assert (await client.patch(f"/api/v1/discussions/{discussion.id}", headers=headers,
                               json={"best_answer_post_id": post.id})).status_code == 200

    lines = texts(await timeline(client, discussion))
    assert "tl_admin3 折叠了 #2 楼" in lines
    assert "tl_admin3 将该讨论设为私密" in lines
    assert "tl_admin3 将 #2 楼设为最佳回复" in lines


async def test_events_fall_on_the_page_of_their_timestamp(session, client) -> None:
    admin = await make_user(session, "tl_admin4", admin=True)
    started = datetime.now(UTC) - timedelta(hours=5)
    discussion = await make_discussion(session, admin, started=started)
    # 第 1 页是 1~20 楼，第 2 页是 21~25 楼
    for number in range(2, 26):
        await make_post(session, discussion, admin, number, started + timedelta(minutes=number))

    headers = auth(client, admin)
    # 夹在第 20、21 楼之间的记录 -> 落在第 1 页
    assert (await client.patch(f"/api/v1/discussions/{discussion.id}", headers=headers,
                               json={"is_sticky": True})).status_code == 200
    sticky = (await session.scalars(
        select(DiscussionEvent).where(DiscussionEvent.discussion_id == discussion.id,
                                      DiscussionEvent.kind == "discussionStickied")
    )).one()
    sticky.created_at = started + timedelta(minutes=20, seconds=30)
    await session.commit()

    # 最后一条回复之后的记录 -> 落在第 2 页
    assert (await client.patch(f"/api/v1/discussions/{discussion.id}", headers=headers,
                               json={"title": "改名"})).status_code == 200

    page1 = await timeline(client, discussion, 1)
    page2 = await timeline(client, discussion, 2)
    assert "tl_admin4 置顶了该讨论" in texts(page1)
    assert "tl_admin4 置顶了该讨论" not in texts(page2)
    assert "tl_admin4 将标题从「t」改为「改名」" in texts(page2)
    assert "tl_admin4 将标题从「t」改为「改名」" not in texts(page1)
