from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import OptionalUser, SessionDep
from app.core.config import settings
from app.models import Discussion, Post, Tag, User
from app.services.visibility import discussion_visible

router = APIRouter(tags=["meta"])


@router.get("/meta")
async def meta(session: SessionDep, user: OptionalUser) -> dict[str, int | str | None]:
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
    untagged = await session.scalar(
        select(func.count()).select_from(Discussion)
        .where(discussion_visible(user), Discussion.is_collapsed.is_(False),
               ~Discussion.tags.any())
    ) or 0
    # 配错了（标签改名/不存在）就当没配，免得首页直接空白
    default_tag = None
    if settings.default_tag:
        default_tag = await session.scalar(
            select(Tag.slug).where(Tag.slug == settings.default_tag)
        )
    return {
        "discussions": discussions, "posts": posts, "users": users,
        "untagged": untagged,
        "timezone": settings.timezone,
        "default_tag": default_tag,
    }
