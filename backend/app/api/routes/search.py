import re

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.deps import SessionDep
from app.models import Discussion, Post
from app.schemas.common import Page
from app.schemas.content import SearchHit, UserBrief

router = APIRouter(tags=["search"])

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def snippet(html: str, keyword: str, width: int = 160) -> str:
    text = _WS.sub(" ", _TAG.sub(" ", html or "")).strip()
    pos = text.lower().find(keyword.lower())
    start = max(0, pos - width // 2) if pos >= 0 else 0
    piece = text[start:start + width]
    return ("…" if start else "") + piece + ("…" if start + width < len(text) else "")


@router.get("/search", response_model=Page[SearchHit])
async def search(
    session: SessionDep,
    q: str = Query(..., min_length=1, max_length=100),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> Page[SearchHit]:
    pattern = f"%{q}%"
    base = (
        select(Post, Discussion.title)
        .join(Discussion, Discussion.id == Post.discussion_id)
        .where(
            Post.body_html.ilike(pattern),
            Post.hidden_at.is_(None),
            Discussion.is_private.is_(False),
        )
    )
    total = await session.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = await session.execute(
        base.order_by(Post.created_at.desc()).limit(per_page).offset((page - 1) * per_page)
    )
    hits = [
        SearchHit(
            post_id=p.id,
            discussion_id=p.discussion_id,
            discussion_title=title,
            number=p.number,
            created_at=p.created_at,
            author=UserBrief.model_validate(p.author) if p.author else None,
            snippet=snippet(p.body_html, q),
        )
        for p, title in rows
    ]
    return Page(items=hits, total=total, page=page, per_page=per_page,
                pages=max(1, -(-total // per_page)))
