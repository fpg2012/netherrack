"""通知的产生规则。"""
from sqlalchemy.dialects.postgresql import insert

from app.models import Discussion, Notification, Post


async def notify(session, *, recipient_id: int | None, actor_id: int, kind: str,
                 discussion_id: int, post_id: int) -> None:
    if recipient_id is None or recipient_id == actor_id:
        return
    stmt = (
        insert(Notification)
        .values(
            recipient_id=recipient_id, actor_id=actor_id, kind=kind,
            discussion_id=discussion_id, post_id=post_id,
        )
        .on_conflict_do_nothing(constraint="uq_notification")
    )
    await session.execute(stmt)


async def notify_reply(session, *, post: Post, discussion: Discussion, actor_id: int,
                       quote: Post | None) -> None:
    """回复通知楼主；如果引用了某层楼，再通知被引用的人。"""
    await notify(session, recipient_id=discussion.author_id, actor_id=actor_id,
                 kind="reply", discussion_id=discussion.id, post_id=post.id)
    if quote is not None:
        await notify(session, recipient_id=quote.author_id, actor_id=actor_id,
                     kind="quote", discussion_id=discussion.id, post_id=post.id)


async def notify_best_answer(session, *, post: Post, actor_id: int) -> None:
    await notify(session, recipient_id=post.author_id, actor_id=actor_id,
                 kind="best_answer", discussion_id=post.discussion_id, post_id=post.id)


async def notify_mentions(session, *, post_id: int, discussion_id: int, actor_id: int,
                          user_ids: list[int], skip: set[int]) -> None:
    for user_id in user_ids:
        if user_id in skip or user_id == actor_id:
            continue
        await notify(session, recipient_id=user_id, actor_id=actor_id,
                     kind="mention", discussion_id=discussion_id, post_id=post_id)
