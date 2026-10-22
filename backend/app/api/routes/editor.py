from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, verify_csrf
from app.schemas.write import EditPost
from app.services.content import render_markdown

router = APIRouter(tags=["editor"])


@router.post("/preview", dependencies=[Depends(verify_csrf)])
async def preview(payload: EditPost, _user: CurrentUser) -> dict[str, str]:
    """Markdown 预览：与正式发帖走同一个渲染 + 清洗函数。"""
    return {"html": render_markdown(payload.body_md)}
