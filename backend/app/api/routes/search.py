from functools import reduce

from fastapi import APIRouter, Query
from sqlalchemy import func, or_, select
from sqlalchemy.sql import ColumnElement

from app.api.deps import SessionDep
from app.models import Discussion, Post
from app.schemas.common import Page
from app.schemas.content import SearchHit, UserBrief
from app.services.search import join_cjk, segment

router = APIRouter(tags=["search"])

HEADLINE = 'MaxWords=30, MinWords=8, ShortWord=1, MaxFragments=1, StartSel="", StopSel=""'


def _tsquery(tokens: list[str], mode: str) -> ColumnElement | None:
    """把分词结果拼成 tsquery：AND 精确，OR 放宽。"""
    parts = [func.plainto_tsquery("simple", t) for t in tokens if t.strip()]
    if not parts:
        return None
    op = " && " if mode == "and" else " || "
    return reduce(lambda a, b: a.op(op)(b), parts)


async def _run(session, tsq: ColumnElement, page: int, per_page: int) -> tuple[int, list]:
    matched = or_(
        Post.search_vector.op("@@")(tsq),
        Discussion.title_vector.op("@@")(tsq),
    )
    base = (
        select(Post, Discussion.title)
        .join(Discussion, Discussion.id == Post.discussion_id)
        .where(Post.hidden_at.is_(None), Discussion.is_private.is_(False), matched)
    )
    total = await session.scalar(select(func.count()).select_from(base.subquery())) or 0
    if total == 0:
        return 0, []

    title_hit = Discussion.title_vector.op("@@")(tsq)
    headline = func.ts_headline(
        "simple",
        func.coalesce(func.nullif(Post.search_text, ""), Post.search_text),
        tsq, HEADLINE,
    )
    rank = (
        func.ts_rank(Post.search_vector, tsq)
        + func.coalesce(func.ts_rank(Discussion.title_vector, tsq), 0) * 0.6
    )
    rows = await session.execute(
        base.add_columns(headline.label("snippet"), title_hit.label("title_hit"))
        .order_by(rank.desc(), Post.created_at.desc())
        .limit(per_page)
        .offset((page - 1) * per_page)
    )
    return total, list(rows)


@router.get("/search", response_model=Page[SearchHit])
async def search(
    session: SessionDep,
    q: str = Query(..., min_length=1, max_length=100),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> Page[SearchHit]:
    tokens = [t for t in segment(q).split() if t]
    tsq = _tsquery(tokens, "and")
    total, rows = (0, [])
    if tsq is not None:
        total, rows = await _run(session, tsq, page, per_page)
        if total == 0:
            # 多个词可能是"或"的关系，放宽后再试一次
            tsq = _tsquery(tokens, "or")
            total, rows = await _run(session, tsq, page, per_page)
    if not rows:
        # 分词后没有有效 token（纯标点等），退回子串匹配
        like = f"%{q}%"
        base = (
            select(Post, Discussion.title)
            .join(Discussion, Discussion.id == Post.discussion_id)
            .where(
                Post.hidden_at.is_(None),
                Discussion.is_private.is_(False),
                or_(Post.search_text.ilike(like), Discussion.search_text.ilike(like)),
            )
        )
        total = await session.scalar(select(func.count()).select_from(base.subquery())) or 0
        rows = [
            (p, title, (p.search_text or "")[:160], False)
            for p, title in (await session.execute(
                base.order_by(Post.created_at.desc()).limit(per_page)
                .offset((page - 1) * per_page)
            ))
        ]

    hits = [
        SearchHit(
            post_id=p.id,
            discussion_id=p.discussion_id,
            discussion_title=title,
            number=p.number,
            created_at=p.created_at,
            author=UserBrief.model_validate(p.author) if p.author else None,
            snippet=join_cjk((snippet or title or "").strip()),
        )
        for p, title, snippet, _ in rows
    ]
    return Page(items=hits, total=total, page=page, per_page=per_page,
                pages=max(1, -(-total // per_page)))
