from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Discussion, Post, User
from app.schemas.common import Page
from app.schemas.content import DiscussionBrief
from app.schemas.user import UserListItem, UserPostItem, UserProfile
from app.services.visibility import discussion_visible

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=Page[UserListItem])
async def list_users(
    session: SessionDep,
    viewer: CurrentUser,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, max_length=64),
) -> Page[UserListItem]:
    post_counts = (
        select(Post.author_id, func.count().label("n"))
        .join(Discussion, Discussion.id == Post.discussion_id)
        .where(Post.hidden_at.is_(None), discussion_visible(viewer))
        .group_by(Post.author_id)
        .subquery()
    )
    discussion_counts = (
        select(Discussion.author_id, func.count().label("n"))
        .where(discussion_visible(viewer))
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


async def _counts(session, user_id: int, viewer) -> tuple[int, int]:
    posts = await session.scalar(
        select(func.count()).select_from(Post)
        .join(Discussion, Discussion.id == Post.discussion_id)
        .where(Post.author_id == user_id, Post.hidden_at.is_(None),
               discussion_visible(viewer))
    ) or 0
    discussions = await session.scalar(
        select(func.count()).select_from(Discussion)
        .where(Discussion.author_id == user_id, discussion_visible(viewer))
    ) or 0
    return posts, discussions


@router.get("/{user_id}", response_model=UserProfile)
async def get_user(user_id: int, session: SessionDep, viewer: CurrentUser) -> UserProfile:
    target = await session.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    posts, discussions = await _counts(session, user_id, viewer)
    return UserProfile(
        id=target.id, username=target.username, nickname=target.nickname,
        avatar_path=target.avatar_path, joined_at=target.joined_at,
        is_admin=target.is_admin, posts=posts, discussions=discussions, bio=target.bio,
    )


@router.get("/{user_id}/discussions", response_model=Page[DiscussionBrief])
async def user_discussions(
    user_id: int,
    session: SessionDep,
    viewer: CurrentUser,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> Page[DiscussionBrief]:
    stmt = (
        select(Discussion)
        .where(Discussion.author_id == user_id, discussion_visible(viewer))
    )
    total = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = await session.scalars(
        stmt.order_by(Discussion.last_posted_at.desc().nullslast())
        .limit(per_page).offset((page - 1) * per_page)
    )
    return Page(items=[DiscussionBrief.model_validate(d) for d in rows], total=total,
                page=page, per_page=per_page, pages=max(1, -(-total // per_page)))


@router.get("/{user_id}/posts", response_model=Page[UserPostItem])
async def user_posts(
    user_id: int,
    session: SessionDep,
    viewer: CurrentUser,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> Page[UserPostItem]:
    base = (
        select(Post, Discussion.title)
        .join(Discussion, Discussion.id == Post.discussion_id)
        .where(Post.author_id == user_id, Post.hidden_at.is_(None),
               discussion_visible(viewer))
    )
    total = await session.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = await session.execute(
        base.order_by(Post.created_at.desc()).limit(per_page).offset((page - 1) * per_page)
    )
    items = [
        UserPostItem(
            post_id=p.id, discussion_id=p.discussion_id, discussion_title=title,
            number=p.number, created_at=p.created_at,
            snippet=(p.search_text or "")[:160],
        )
        for p, title in rows
    ]
    return Page(items=items, total=total, page=page, per_page=per_page,
                pages=max(1, -(-total // per_page)))
