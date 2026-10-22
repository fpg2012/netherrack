from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import SessionDep
from app.models import Discussion, DiscussionTag, Tag
from app.schemas.content import TagWithCount

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagWithCount])
async def list_tags(session: SessionDep) -> list[TagWithCount]:
    counts = (
        select(DiscussionTag.tag_id, func.count().label("n"))
        .join(Discussion, Discussion.id == DiscussionTag.discussion_id)
        .where(Discussion.is_private.is_(False))
        .group_by(DiscussionTag.tag_id)
        .subquery()
    )
    rows = await session.execute(
        select(Tag, func.coalesce(counts.c.n, 0))
        .outerjoin(counts, counts.c.tag_id == Tag.id)
        .order_by(Tag.position, Tag.name)
    )
    return [
        TagWithCount(id=t.id, name=t.name, slug=t.slug, color=t.color, is_qna=t.is_qna, count=n)
        for t, n in rows
    ]
