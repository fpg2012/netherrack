
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
    return FileResponse(target, headers={"Cache-Control": "public, max-age=604800"})
