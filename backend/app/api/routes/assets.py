
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.core.config import settings

router = APIRouter(tags=["assets"])


@router.get("/media/{path:path}")
async def get_asset(path: str) -> FileResponse:
    root = settings.assets_dir.resolve()
    target = (root / path).resolve()
    # 防目录穿越
    if not target.is_relative_to(root) or not target.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "文件不存在")
    headers = {
        "Cache-Control": "public, max-age=604800",
        # 用户上传的内容一律禁止浏览器猜 MIME，避免被当成 HTML 执行
        "X-Content-Type-Options": "nosniff",
    }
    if target.suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf"}:
        headers["Content-Disposition"] = f'attachment; filename="{target.name}"'
    return FileResponse(target, headers=headers)
