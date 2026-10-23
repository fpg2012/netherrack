"""极简的进程内事件总线：给 SSE 推送「有新通知」的信号。

只推失效信号，不推内容——前端收到后照旧调接口拉未读数/列表。
单进程够用；多 worker 时每个进程只知道自己的连接，需要换成
Postgres LISTEN/NOTIFY 或 Redis 才能跨进程广播（见 DEPLOY.md）。
"""
import asyncio
import contextlib
from collections import defaultdict

from sqlalchemy import event
from sqlalchemy.orm import Session

# user_id -> 该用户所有在线连接的队列
_subscribers: dict[int, set[asyncio.Queue[None]]] = defaultdict(set)


def subscribe(user_id: int) -> asyncio.Queue[None]:
    queue: asyncio.Queue[None] = asyncio.Queue(maxsize=1)
    _subscribers[user_id].add(queue)
    return queue


def unsubscribe(user_id: int, queue: asyncio.Queue[None]) -> None:
    queues = _subscribers.get(user_id)
    if not queues:
        return
    queues.discard(queue)
    if not queues:
        _subscribers.pop(user_id, None)


def publish(user_id: int) -> None:
    for queue in list(_subscribers.get(user_id, ())):
        with contextlib.suppress(asyncio.QueueFull):
            queue.put_nowait(None)


def mark_notified(session: Session | object, user_ids: set[int] | list[int]) -> None:
    """把收件人记在 session 上，提交成功后再推送，避免推出未落库的通知。"""
    if not user_ids:
        return
    pending = session.info.setdefault("notify_users", set())  # type: ignore[attr-defined]
    pending.update(user_ids)


@event.listens_for(Session, "after_commit")
def _publish_after_commit(session: Session) -> None:
    for user_id in session.info.pop("notify_users", ()):
        publish(user_id)


@event.listens_for(Session, "after_rollback")
def _drop_after_rollback(session: Session) -> None:
    session.info.pop("notify_users", None)
