from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import CurrentUser, SessionDep, verify_csrf
from app.core.ratelimit import limiter
from app.models import Discussion, Post
from app.schemas.content import PostOut
from app.schemas.write import CollapsePost, EditPost
from app.services.content import render_markdown
from app.services.search import index_text

router = APIRouter(prefix="/posts", tags=["posts"])


async def _get_editable(post_id: int, user, session) -> Post:
    post = await session.get(Post, post_id)
    if post is None or post.hidden_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "帖子不存在")
    if post.author_id != user.id and not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "只能编辑自己的帖子")
    if post.is_legacy:
        raise HTTPException(status.HTTP_409_CONFLICT, "迁移过来的旧帖子不支持编辑")
    return post


@router.patch("/{post_id}", response_model=PostOut, dependencies=[Depends(verify_csrf)])
@limiter.limit("60/hour")
async def edit_post(request: Request, post_id: int, payload: EditPost, session: SessionDep,
                    user: CurrentUser) -> PostOut:
    post = await _get_editable(post_id, user, session)
    post.body_md = payload.body_md
    post.body_html = render_markdown(payload.body_md)
    post.search_text = index_text(post.body_html)
    post.edited_at = datetime.now(UTC)
    post.edited_by_id = user.id
    await session.commit()
    await session.refresh(post, ["author"])
    return PostOut.model_validate(post)


@router.delete("/{post_id}", status_code=204, dependencies=[Depends(verify_csrf)])
async def hide_post(post_id: int, session: SessionDep, user: CurrentUser) -> None:
    post = await session.get(Post, post_id)
    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "帖子不存在")
    if post.author_id != user.id and not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "无权删除")
    post.hidden_at = datetime.now(UTC)
    discussion = await session.get(Discussion, post.discussion_id)
    if discussion:
        discussion.post_count = max(0, discussion.post_count - 1)
    await session.commit()


@router.patch("/{post_id}/collapse", response_model=PostOut,
              dependencies=[Depends(verify_csrf)])
@limiter.limit("120/hour")
async def collapse_post(request: Request, post_id: int, payload: CollapsePost,
                        session: SessionDep, user: CurrentUser) -> PostOut:
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "只有管理员可以折叠")
    post = await session.get(Post, post_id)
    if post is None or post.hidden_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "帖子不存在")
    if post.is_collapsed != payload.is_collapsed:
        post.is_collapsed = payload.is_collapsed
        await session.commit()
    await session.refresh(post, ["author"])
    out = PostOut.model_validate(post)
    if post.is_collapsed:
        out.body_html = ""
        out.body_md = None
    return out
