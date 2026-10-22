from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.deps import SessionDep
from app.models import Discussion, Post, User
from app.schemas.common import Page
from app.schemas.user import UserListItem

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=Page[UserListItem])
async def list_users(
    session: SessionDep,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, max_length=64),
) -> Page[UserListItem]:
    post_counts = (
        select(Post.author_id, func.count().label("n"))
        .where(Post.hidden_at.is_(None))
        .group_by(Post.author_id)
        .subquery()
    )
    discussion_counts = (
        select(Discussion.author_id, func.count().label("n"))
        .where(Discussion.is_private.is_(False))
        .group_by(Discussion.author_id)
        .subquery()
    )

    stmt = (
        select(
            User,
            func.coalesce(post_counts.c.n, 0),
            func.coalesce(discussion_counts.c.n, 0),
        )
        .outerjoin(post_counts, post_counts.c.author_id == User.id)
        .outerjoin(discussion_counts, discussion_counts.c.author_id == User.id)
    )
    if q:
        stmt = stmt.where(User.username.ilike(f"%{q}%"))

    total = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = await session.execute(
        stmt.order_by(User.joined_at).limit(per_page).offset((page - 1) * per_page)
    )
    items = [
        UserListItem(
            id=u.id, username=u.username, nickname=u.nickname, avatar_path=u.avatar_path,
            joined_at=u.joined_at, is_admin=u.is_admin, posts=posts, discussions=discussions,
        )
        for u, posts, discussions in rows
    ]
    return Page(items=items, total=total, page=page, per_page=per_page,
                pages=max(1, -(-total // per_page)))
