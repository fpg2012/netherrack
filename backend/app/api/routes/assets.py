from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.api.deps import OptionalUser, SessionDep
from app.core.config import settings
from app.models import Discussion, Post

router = APIRouter(tags=["assets"])

PUBLIC_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif",
    ".mp4", ".webm", ".mp3", ".ogg", ".wav",
}


@router.get("/media/{path:path}")
async def get_asset(path: str, session: SessionDep, user: OptionalUser) -> FileResponse:
    root = settings.assets_dir.resolve()
    target = (root / path).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "文件不存在")

    # 帖子附件：游客只能看「公开讨论里引用过」的文件
    if path.startswith("files/") and user is None:
        referenced = await session.scalar(
            select(Post.id)
            .join(Discussion, Discussion.id == Post.discussion_id)
            .where(
                Discussion.is_public.is_(True),
                Post.body_html.contains(Path(path).name),
            )
            .limit(1)
        )
        if referenced is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "请先登录")

    headers = {
        "Cache-Control": "public, max-age=604800",
        # 用户上传的内容禁止浏览器猜 MIME，避免被当成 HTML 执行
        "X-Content-Type-Options": "nosniff",
    }
    if target.suffix.lower() not in PUBLIC_SUFFIXES:
        headers["Content-Disposition"] = f'attachment; filename="{target.name}"'
    return FileResponse(target, headers=headers)
