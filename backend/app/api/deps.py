from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import csrf_matches, decode_token
from app.db.session import get_session
from app.models import User

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    session: SessionDep,
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    if not access_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "未登录")
    payload = decode_token(access_token, "access")
    if payload is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "登录已过期")
    from app.models import RevokedToken

    revoked = await session.scalar(
        select(RevokedToken.id).where(RevokedToken.jti == payload.get("jti"))
    )
    if revoked:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "已登出")
    user = await session.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "账号不可用")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def verify_csrf(
    csrf_token: Annotated[str | None, Cookie()] = None,
    x_csrf_token: Annotated[str | None, Header()] = None,
) -> None:
    """双提交校验：cookie 与请求头里的 CSRF token 必须一致。"""
    if not csrf_matches(csrf_token, x_csrf_token):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "CSRF 校验失败")
