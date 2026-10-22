from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import csrf_matches, decode_token
from app.db.session import get_session
from app.models import RevokedToken, User

SessionDep = Annotated[AsyncSession, Depends(get_session)]
AccessCookie = Annotated[str | None, Cookie()]


async def _user_from_token(session: AsyncSession, token: str | None) -> User | None:
    if not token:
        return None
    payload = decode_token(token, "access")
    if payload is None:
        return None
    revoked = await session.scalar(
        select(RevokedToken.id).where(RevokedToken.jti == payload.get("jti"))
    )
    if revoked:
        return None
    user = await session.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        return None
    return user


async def get_current_user(session: SessionDep, access_token: AccessCookie = None) -> User:
    user = await _user_from_token(session, access_token)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "请先登录")
    return user


async def get_optional_user(session: SessionDep, access_token: AccessCookie = None) -> User | None:
    return await _user_from_token(session, access_token)


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]


async def verify_csrf(
    csrf_token: Annotated[str | None, Cookie()] = None,
    x_csrf_token: Annotated[str | None, Header()] = None,
) -> None:
    """双提交校验：cookie 与请求头里的 CSRF token 必须一致。"""
    if not csrf_matches(csrf_token, x_csrf_token):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "CSRF 校验失败")
