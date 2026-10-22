from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, OptionalUser, SessionDep, verify_csrf
from app.core.ratelimit import limiter
from app.models import Discussion, DiscussionEvent, DiscussionTag, Post, Tag
from app.schemas.common import Page
from app.schemas.content import (
    DiscussionBrief,
    DiscussionDetail,
    EventOut,
    PostOut,
    TimelineItem,
)
from app.schemas.write import EditDiscussion, NewDiscussion, NewPost
from app.services.content import event_text, render_markdown
from app.services.quote import build_quote
from app.services.search import index_text, segment
from app.services.visibility import can_view, discussion_visible

router = APIRouter(prefix="/discussions", tags=["discussions"])


@router.get("", response_model=Page[DiscussionBrief])
async def list_discussions(
    session: SessionDep,
    user: OptionalUser,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    tag: str | None = None,
    q: str | None = None,
) -> Page[DiscussionBrief]:
    stmt = select(Discussion).where(discussion_visible(user))
    if tag:
        stmt = stmt.where(
            Discussion.id.in_(
                select(DiscussionTag.discussion_id)
                .join(Tag, Tag.id == DiscussionTag.tag_id)
                .where(Tag.slug == tag)
            )
        )
    if q:
        stmt = stmt.where(Discussion.title.ilike(f"%{q}%"))

    total = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    # 置顶是「板块内」的概念：只有筛了标签才把置顶提到前面，
    # 「全部」按最后回复时间排，否则置顶帖会永远霸占首页
    order = [Discussion.last_posted_at.desc().nullslast()]
    if tag:
        order.insert(0, Discussion.is_sticky.desc())

    rows = await session.scalars(
        stmt.options(selectinload(Discussion.tags))
        .order_by(*order)
        .limit(per_page)
        .offset((page - 1) * per_page)
    )
    items = [DiscussionBrief.model_validate(d) for d in rows]
    return Page(items=items, total=total, page=page, per_page=per_page,
                pages=max(1, -(-total // per_page)))


@router.get("/{discussion_id}", response_model=DiscussionDetail)
async def get_discussion(discussion_id: int, session: SessionDep,
                         user: OptionalUser) -> DiscussionDetail:
    discussion = await session.get(Discussion, discussion_id)
    if discussion is None or not can_view(discussion, user):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")
    await session.refresh(discussion, ["tags"])
    return DiscussionDetail.model_validate(discussion)


@router.get("/{discussion_id}/timeline", response_model=Page[TimelineItem])
async def timeline(
    discussion_id: int,
    session: SessionDep,
    user: OptionalUser,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> Page[TimelineItem]:
    """帖子按楼层号分页，夹在其中的操作记录一起返回，保持时间顺序。"""
    discussion = await session.get(Discussion, discussion_id)
    if discussion is None or not can_view(discussion, user):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")

    total = await session.scalar(
        select(func.count()).select_from(Post)
        .where(Post.discussion_id == discussion_id, Post.hidden_at.is_(None))
    ) or 0
    posts = (await session.scalars(
        select(Post)
        .where(Post.discussion_id == discussion_id, Post.hidden_at.is_(None))
        .order_by(Post.number)
        .limit(per_page)
        .offset((page - 1) * per_page)
    )).all()

    events: list[DiscussionEvent] = []
    if posts:
        events = list(await session.scalars(
            select(DiscussionEvent)
            .where(
                DiscussionEvent.discussion_id == discussion_id,
                DiscussionEvent.created_at >= posts[0].created_at,
                DiscussionEvent.created_at <= posts[-1].created_at,
            )
            .order_by(DiscussionEvent.created_at)
        ))

    names = {t.id: t.name for t in await session.scalars(select(Tag))}
    items: list[TimelineItem] = []
    for p in posts:
        items.append(TimelineItem(
            type="post", id=p.id, created_at=p.created_at,
            post=PostOut.model_validate(p),
        ))
    for e in events:
        who = "匿名"
        if e.actor is not None:
            who = e.actor.nickname or e.actor.username
        items.append(TimelineItem(
            type="event", id=e.id, created_at=e.created_at,
            event=EventOut(id=e.id, kind=e.kind,
                           text=event_text(e.kind, e.payload, who, names),
                           created_at=e.created_at),
        ))
    items.sort(key=lambda i: i.created_at)

    return Page[TimelineItem](items=items, total=total, page=page, per_page=per_page,
                              pages=max(1, -(-total // per_page)))


# ---------------------------------------------------------------- 写操作

async def _tags_by_slug(session, slugs: list[str]) -> list[Tag]:
    if not slugs:
        return []
    rows = list(await session.scalars(select(Tag).where(Tag.slug.in_(slugs))))
    if len(rows) != len(set(slugs)):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "包含不存在的标签")
    return rows


def _record(session, discussion_id: int, actor_id: int, kind: str, payload: dict) -> None:
    session.add(DiscussionEvent(
        discussion_id=discussion_id, actor_id=actor_id, kind=kind, payload=payload,
    ))


@router.post("", response_model=DiscussionDetail, status_code=201,
             dependencies=[Depends(verify_csrf)])
@limiter.limit("10/hour")
async def create_discussion(request: Request, payload: NewDiscussion, session: SessionDep,
                            user: CurrentUser) -> DiscussionDetail:
    tags = await _tags_by_slug(session, payload.tags)
    now = datetime.now(UTC)
    discussion = Discussion(
        title=payload.title,
        search_text=segment(payload.title),
        author_id=user.id,
        created_at=now,
        last_posted_at=now,
        tags=tags,
    )
    session.add(discussion)
    await session.flush()

    html = render_markdown(payload.body_md)
    post = Post(
        discussion_id=discussion.id,
        number=1,
        author_id=user.id,
        body_md=payload.body_md,
        body_html=html,
        search_text=index_text(html),
        created_at=now,
    )
    session.add(post)
    await session.flush()

    discussion.post_count = 1
    await session.commit()
    await session.refresh(discussion, ["tags", "author"])
    return DiscussionDetail.model_validate(discussion)


@router.post("/{discussion_id}/posts", response_model=PostOut, status_code=201,
             dependencies=[Depends(verify_csrf)])
@limiter.limit("30/hour")
async def reply(request: Request, discussion_id: int, payload: NewPost, session: SessionDep,
                user: CurrentUser) -> PostOut:
    # 锁定行，保证楼层号并发安全
    # 只锁 discussions 这一张表：author 是 joined 预加载，锁整行会命中外连接
    discussion = await session.scalar(
        select(Discussion).where(Discussion.id == discussion_id)
        .with_for_update(of=Discussion)
    )
    if discussion is None or not can_view(discussion, user):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")
    if discussion.is_locked and not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "讨论已锁定")

    number = (await session.scalar(
        select(func.coalesce(func.max(Post.number), 0)).where(
            Post.discussion_id == discussion_id)
    )) + 1

    body_md = payload.body_md
    if payload.quote_post_id:
        quoted = await session.get(Post, payload.quote_post_id)
        if quoted is None or quoted.discussion_id != discussion_id:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "引用的帖子不在该讨论中")
        body_md = build_quote(quoted) + "\n\n" + body_md

    html = render_markdown(body_md)
    post = Post(
        discussion_id=discussion_id, number=number, author_id=user.id,
        body_md=body_md, body_html=html, search_text=index_text(html),
        created_at=datetime.now(UTC),
    )
    session.add(post)
    discussion.post_count += 1
    discussion.last_posted_at = post.created_at
    await session.commit()
    await session.refresh(post, ["author"])
    return PostOut.model_validate(post)


@router.patch("/{discussion_id}", response_model=DiscussionDetail,
              dependencies=[Depends(verify_csrf)])
async def edit_discussion(discussion_id: int, payload: EditDiscussion, session: SessionDep,
                          user: CurrentUser) -> DiscussionDetail:
    # 只锁 discussions 这一张表：author 是 joined 预加载，锁整行会命中外连接
    discussion = await session.scalar(
        select(Discussion).where(Discussion.id == discussion_id)
        .with_for_update(of=Discussion)
    )
    if discussion is None or not can_view(discussion, user):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")

    is_owner = discussion.author_id == user.id
    admin_only = any(v is not None for v in (
        payload.is_sticky, payload.is_locked, payload.best_answer_post_id,
        payload.is_public))
    if not user.is_admin and not (is_owner and not admin_only):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "无权修改该讨论")

    if payload.title and payload.title != discussion.title:
        _record(session, discussion.id, user.id, "discussionRenamed",
                {"old": discussion.title, "new": payload.title})
        discussion.title = payload.title
        discussion.search_text = segment(payload.title)

    if payload.is_sticky is not None and payload.is_sticky != discussion.is_sticky:
        discussion.is_sticky = payload.is_sticky
        _record(session, discussion.id, user.id, "discussionStickied",
                {"sticky": payload.is_sticky})

    if payload.is_locked is not None and payload.is_locked != discussion.is_locked:
        discussion.is_locked = payload.is_locked
        _record(session, discussion.id, user.id, "discussionLocked",
                {"locked": payload.is_locked})

    if payload.tags is not None:
        tags = await _tags_by_slug(session, payload.tags)
        old = {t.id for t in discussion.tags}
        new = {t.id for t in tags}
        if old != new:
            discussion.tags = tags
            _record(session, discussion.id, user.id, "discussionTagged",
                    {"added": sorted(new - old), "removed": sorted(old - new)})

    if payload.is_public is not None and payload.is_public != discussion.is_public:
        discussion.is_public = payload.is_public

    if payload.best_answer_post_id is not None:
        post = await session.get(Post, payload.best_answer_post_id)
        if post is None or post.discussion_id != discussion.id:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "最佳回复不属于该讨论")
        discussion.best_answer_post_id = post.id

    await session.commit()
    await session.refresh(discussion, ["tags", "author"])
    return DiscussionDetail.model_validate(discussion)
