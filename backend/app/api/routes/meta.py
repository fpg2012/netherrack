from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import SessionDep
from app.models import Discussion, Post, User

router = APIRouter(tags=["meta"])


@router.get("/meta")
async def meta(session: SessionDep) -> dict[str, int]:
    discussions = await session.scalar(
        select(func.count()).select_from(Discussion).where(Discussion.is_private.is_(False))
    ) or 0
    posts = await session.scalar(select(func.count()).select_from(Post)) or 0
    users = await session.scalar(select(func.count()).select_from(User)) or 0
    return {"discussions": discussions, "posts": posts, "users": users}
