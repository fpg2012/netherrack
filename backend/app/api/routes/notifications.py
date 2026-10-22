from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, SessionDep, verify_csrf
from app.models import Discussion, Notification, Post
from app.schemas.common import Page
from app.schemas.content import UserBrief
from app.schemas.notification import NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=Page[NotificationOut])
async def list_notifications(
    session: SessionDep,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> Page[NotificationOut]:
    base = (
        select(Notification, Discussion.title, Post.number)
        .join(Discussion, Discussion.id == Notification.discussion_id)
        .outerjoin(Post, Post.id == Notification.post_id)
        .where(Notification.recipient_id == user.id)
    )
    total = await session.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = await session.execute(
        base.order_by(Notification.created_at.desc())
        .limit(per_page)
        .offset((page - 1) * per_page)
    )
    items = [
        NotificationOut(
            id=n.id,
            kind=n.kind,
            discussion_id=n.discussion_id,
            discussion_title=title,
            post_id=n.post_id,
            post_number=number,
            actor=UserBrief.model_validate(n.actor) if n.actor else None,
            read=n.read_at is not None,
            created_at=n.created_at,
        )
        for n, title, number in rows
    ]
    return Page(items=items, total=total, page=page, per_page=per_page,
                pages=max(1, -(-total // per_page)))


@router.get("/unread")
async def unread_count(session: SessionDep, user: CurrentUser) -> dict[str, int]:
    count = await session.scalar(
        select(func.count()).select_from(Notification).where(
            Notification.recipient_id == user.id, Notification.read_at.is_(None)
        )
    ) or 0
    return {"count": count}


@router.post("/read-all", dependencies=[Depends(verify_csrf)])
async def read_all(session: SessionDep, user: CurrentUser) -> dict[str, int]:
    rows = (
        await session.scalars(
            select(Notification).where(
                Notification.recipient_id == user.id, Notification.read_at.is_(None)
            )
        )
    ).all()
    now = datetime.now(UTC)
    for notification in rows:
        notification.read_at = now
    await session.commit()
    return {"updated": len(rows)}


@router.post("/{notification_id}/read", status_code=204, dependencies=[Depends(verify_csrf)])
async def mark_read(notification_id: int, session: SessionDep, user: CurrentUser) -> None:
    notification = await session.get(Notification, notification_id)
    if notification is None or notification.recipient_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "通知不存在")
    if notification.read_at is None:
        notification.read_at = datetime.now(UTC)
        await session.commit()
