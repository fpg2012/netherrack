import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from pydantic import BaseModel

from app.api.deps import CurrentUser, SessionDep, verify_csrf
from app.core.config import settings
from app.core.ratelimit import limiter
from app.models import Upload

router = APIRouter(prefix="/uploads", tags=["uploads"])

# 只放行这几类：图片、PDF、纯文本、压缩包。
# 不放 SVG/HTML —— 同源返回会变成存储型 XSS。
ALLOWED = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".md": "text/plain",
    ".zip": "application/zip",
}
MAX_BYTES = 10 * 1024 * 1024
CHUNK = 64 * 1024
_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


class UploadOut(BaseModel):
    uuid: str
    url: str
    filename: str
    size: int
    mime: str


@router.post("", response_model=UploadOut, status_code=201, dependencies=[Depends(verify_csrf)])
@limiter.limit("20/hour")
async def upload(request: Request, file: UploadFile, session: SessionDep,
                 user: CurrentUser) -> UploadOut:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"不支持的文件类型，允许：{', '.join(sorted(ALLOWED))}",
        )

    now = datetime.now(UTC)
    rel_dir = Path("files") / now.strftime("%Y-%m-%d")
    target_dir = settings.assets_dir / rel_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    stem = _SAFE.sub("-", Path(file.filename or "file").stem)[:60] or "file"
    uid = str(uuid.uuid4())
    name = f"{uid}-{stem}{suffix}"
    target = target_dir / name

    size = 0
    try:
        with target.open("wb") as out:
            while chunk := await file.read(CHUNK):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                                        f"文件超过 {MAX_BYTES // 1024 // 1024} MB")
                out.write(chunk)
    except Exception:
        target.unlink(missing_ok=True)
        raise

    upload = Upload(
        uuid=uid,
        path=str(rel_dir / name),
        filename=file.filename or name,
        size=size,
        mime=ALLOWED[suffix],
        uploader_id=user.id,
    )
    session.add(upload)
    await session.commit()

    return UploadOut(
        uuid=uid,
        url=f"/media/{upload.path}",
        filename=upload.filename,
        size=size,
        mime=upload.mime or ALLOWED[suffix],
    )
