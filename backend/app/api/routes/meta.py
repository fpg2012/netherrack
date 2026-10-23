from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import OptionalUser, SessionDep
from app.core.config import settings
from app.models import Discussion, Post, User
from app.services.visibility import discussion_visible

router = APIRouter(tags=["meta"])


@router.get("/meta")
async def meta(session: SessionDep, user: OptionalUser) -> dict[str, int | str]:
    discussions = await session.scalar(
        select(func.count()).select_from(Discussion)
        .where(discussion_visible(user), Discussion.is_collapsed.is_(False))
    ) or 0
    posts = await session.scalar(
        select(func.count()).select_from(Post)
        .join(Discussion, Discussion.id == Post.discussion_id)
        .where(discussion_visible(user), Discussion.is_collapsed.is_(False))
    ) or 0
    users = await session.scalar(select(func.count()).select_from(User)) or 0
    return {
        "discussions": discussions, "posts": posts, "users": users,
        "timezone": settings.timezone,
    }
