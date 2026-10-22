from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, SessionDep, verify_csrf
from app.schemas.write import EditPost
from app.services.content import render_markdown
from app.services.mentions import link_mentions, username_map

router = APIRouter(tags=["editor"])


@router.post("/preview", dependencies=[Depends(verify_csrf)])
async def preview(payload: EditPost, session: SessionDep, _user: CurrentUser) -> dict[str, str]:
    """Markdown 预览：与正式发帖走同一个渲染 + 清洗函数。"""
    html, _ = link_mentions(render_markdown(payload.body_md), await username_map(session))
    return {"html": html}
