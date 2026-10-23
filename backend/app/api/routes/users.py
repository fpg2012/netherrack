import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import delete, func, select

from app.api.deps import CurrentUser, SessionDep, verify_csrf
from app.core.config import settings
from app.core.ratelimit import limiter
from app.core.security import hash_password, verify_password
from app.models import Discussion, Post, RefreshToken, User
from app.schemas.common import Page
from app.schemas.content import DiscussionBrief
from app.schemas.user import (
    PasswordChange,
    ProfileUpdate,
    UserListItem,
    UserPostItem,
    UserProfile,
)
from app.services.audit import audit
from app.services.content import plain_text
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
        .where(Post.hidden_at.is_(None), Post.is_collapsed.is_(False),
               discussion_visible(viewer), Discussion.is_collapsed.is_(False))
        .group_by(Post.author_id)
        .subquery()
    )
    discussion_counts = (
        select(Discussion.author_id, func.count().label("n"))
        .where(discussion_visible(viewer), Discussion.is_collapsed.is_(False))
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


@router.patch("/me", response_model=UserProfile, dependencies=[Depends(verify_csrf)])
async def update_me(
    payload: ProfileUpdate, session: SessionDep, viewer: CurrentUser
) -> UserProfile:
    changed = []
    if payload.nickname is not None:
        nickname = payload.nickname.strip()
        if len(nickname) > 32:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "昵称最多 32 个字")
        viewer.nickname = nickname or None
        changed.append("nickname")
    if payload.bio is not None:
        bio = payload.bio.strip()
        if len(bio) > 500:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "自我介绍最多 500 个字")
        viewer.bio = bio or None
        changed.append("bio")
    if changed:
        await audit(session, actor_id=viewer.id, action="profile.update",
                    target_type="user", target_id=viewer.id, fields=changed)
    await session.commit()
    posts, discussions = await _counts(session, viewer.id, viewer)
    return UserProfile(
        id=viewer.id, username=viewer.username, nickname=viewer.nickname,
        avatar_path=viewer.avatar_path, joined_at=viewer.joined_at,
        is_admin=viewer.is_admin, posts=posts, discussions=discussions, bio=viewer.bio,
    )


AVATAR_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif"}

_MAGIC = {
    b"\x89PNG\r\n\x1a\n": {".png"},
    b"\xff\xd8\xff": {".jpg", ".jpeg"},
    b"GIF87a": {".gif"},
    b"GIF89a": {".gif"},
}


def _looks_like_image(head: bytes, suffix: str) -> bool:
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return suffix == ".webp"
    # AVIF：ISOBMFF 容器，brand 在偏移 8
    if head[4:8] == b"ftyp" and head[8:12] in {b"avif", b"avis"}:
        return suffix == ".avif"
    return any(head.startswith(magic) and suffix in suffixes for magic, suffixes in _MAGIC.items())


@router.post("/me/avatar", response_model=UserProfile,
             dependencies=[Depends(verify_csrf)])
@limiter.limit("20/hour")
async def upload_avatar(
    request: Request, file: UploadFile, session: SessionDep, viewer: CurrentUser
) -> UserProfile:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in AVATAR_SUFFIXES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"头像只支持 {', '.join(sorted(AVATAR_SUFFIXES))}",
        )

    target_dir = settings.assets_dir / "avatars"
    target_dir.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{suffix}"
    target = target_dir / name

    size = 0
    first = True
    try:
        with target.open("wb") as out:
            while chunk := await file.read(64 * 1024):
                if first:
                    if not _looks_like_image(chunk[:12], suffix):
                        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                                            "文件内容不是有效的图片")
                    first = False
                size += len(chunk)
                if size > settings.avatar_max_bytes:
                    limit = settings.avatar_max_bytes / 1024 / 1024
                    raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                                        f"头像不能超过 {limit:g} MB")
                out.write(chunk)
    except Exception:
        target.unlink(missing_ok=True)
        raise

    viewer.avatar_path = name
    await audit(session, actor_id=viewer.id, action="avatar.update",
                target_type="user", target_id=viewer.id, file=name)
    await session.commit()
    posts, discussions = await _counts(session, viewer.id, viewer)
    return UserProfile(
        id=viewer.id, username=viewer.username, nickname=viewer.nickname,
        avatar_path=viewer.avatar_path, joined_at=viewer.joined_at,
        is_admin=viewer.is_admin, posts=posts, discussions=discussions, bio=viewer.bio,
    )


@router.post("/me/password", status_code=204, dependencies=[Depends(verify_csrf)])
@limiter.limit("10/hour")
async def change_password(
    request: Request, payload: PasswordChange, session: SessionDep, viewer: CurrentUser
) -> None:
    ok, _ = verify_password(payload.current_password, viewer.password_hash)
    if not ok:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "当前密码不正确")
    if payload.new_password == payload.current_password:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "新密码不能和旧密码相同")
    await audit(session, actor_id=viewer.id, action="account.password",
                target_type="user", target_id=viewer.id)
    viewer.password_hash = hash_password(payload.new_password)
    # 改密码后让其他设备上的会话失效
    await session.execute(delete(RefreshToken).where(RefreshToken.user_id == viewer.id))
    await session.commit()


async def _counts(session, user_id: int, viewer) -> tuple[int, int]:
    posts = await session.scalar(
        select(func.count()).select_from(Post)
        .join(Discussion, Discussion.id == Post.discussion_id)
        .where(Post.author_id == user_id, Post.hidden_at.is_(None),
               Post.is_collapsed.is_(False),
               discussion_visible(viewer), Discussion.is_collapsed.is_(False))
    ) or 0
    discussions = await session.scalar(
        select(func.count()).select_from(Discussion)
        .where(Discussion.author_id == user_id,
               discussion_visible(viewer), Discussion.is_collapsed.is_(False))
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
        .where(Discussion.author_id == user_id,
               discussion_visible(viewer), Discussion.is_collapsed.is_(False))
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
               Post.is_collapsed.is_(False),
               discussion_visible(viewer), Discussion.is_collapsed.is_(False))
    )
    total = await session.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = await session.execute(
        base.order_by(Post.created_at.desc()).limit(per_page).offset((page - 1) * per_page)
    )
    items = [
        UserPostItem(
            post_id=p.id, discussion_id=p.discussion_id, discussion_title=title,
            number=p.number, created_at=p.created_at,
            snippet=plain_text(p.body_html)[:160],
        )
        for p, title in rows
    ]
    return Page(items=items, total=total, page=page, per_page=per_page,
                pages=max(1, -(-total // per_page)))
