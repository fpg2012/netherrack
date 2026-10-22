from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import delete, select

from app.api.deps import CurrentUser, SessionDep, verify_csrf
from app.core.config import settings
from app.core.security import (
    create_token,
    decode_token,
    hash_password,
    hash_token,
    new_csrf_token,
    verify_password,
)
from app.models import RefreshToken, RevokedToken, User
from app.schemas.auth import LoginIn, LoginOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_OPTS = dict(
    httponly=True, secure=settings.cookie_secure, samesite=settings.cookie_samesite
)


def _set_cookies(response: Response, access: str, refresh: str, csrf: str) -> None:
    response.set_cookie("access_token", access, max_age=settings.access_token_ttl,
                        path="/", **COOKIE_OPTS)
    response.set_cookie("refresh_token", refresh, max_age=settings.refresh_token_ttl,
                        path="/api/v1/auth", **COOKIE_OPTS)
    # CSRF token 要被前端读取，所以不能 httponly
    response.set_cookie("csrf_token", csrf, max_age=settings.refresh_token_ttl, path="/",
                        secure=settings.cookie_secure, samesite=settings.cookie_samesite)


async def _issue(session, user: User, response: Response, user_agent: str | None) -> str:
    access = create_token(str(user.id), "access", settings.access_token_ttl)
    refresh = create_token(str(user.id), "refresh", settings.refresh_token_ttl)
    csrf = new_csrf_token()
    session.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh),
        expires_at=datetime.now(UTC) + timedelta(seconds=settings.refresh_token_ttl),
        user_agent=(user_agent or "")[:255] or None,
    ))
    await session.commit()
    _set_cookies(response, access, refresh, csrf)
    return csrf


@router.post("/login", response_model=LoginOut)
async def login(payload: LoginIn, request: Request, response: Response,
                session: SessionDep) -> LoginOut:
    user = await session.scalar(select(User).where(User.username == payload.username))
    # 无论用户是否存在都走一遍校验，避免通过响应时间枚举用户名
    ok, needs_rehash = (False, False) if user is None else verify_password(
        payload.password, user.password_hash)
    if user is None or not user.is_active or not ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户名或密码错误")
    if needs_rehash:                      # bcrypt -> argon2
        user.password_hash = hash_password(payload.password)
    csrf = await _issue(session, user, response, request.headers.get("user-agent"))
    return LoginOut(user=UserOut.model_validate(user), csrf_token=csrf)


@router.post("/refresh", response_model=UserOut)
async def refresh(
    request: Request,
    response: Response,
    session: SessionDep,
    _: Annotated[None, Depends(verify_csrf)],
    refresh_cookie: Annotated[str | None, Cookie(alias="refresh_token")] = None,
) -> UserOut:
    payload = decode_token(refresh_cookie, "refresh") if refresh_cookie else None
    if payload is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "refresh token 无效")
    row = await session.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_cookie))
    )
    if row is None or row.revoked_at is not None or row.expires_at < datetime.now(UTC):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "refresh token 已失效")
    user = await session.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "账号不可用")

    row.revoked_at = datetime.now(UTC)      # 轮换，旧的立刻作废
    await _issue(session, user, response, request.headers.get("user-agent"))
    return UserOut.model_validate(user)


@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    session: SessionDep,
    _: Annotated[None, Depends(verify_csrf)],
    refresh_cookie: Annotated[str | None, Cookie(alias="refresh_token")] = None,
    access_cookie: Annotated[str | None, Cookie(alias="access_token")] = None,
) -> None:
    # 立即失效当前 access token（否则它在 TTL 内仍然可用）
    payload = decode_token(access_cookie, "access") if access_cookie else None
    if payload:
        session.add(RevokedToken(
            jti=payload["jti"],
            expires_at=datetime.fromtimestamp(payload["exp"], UTC),
        ))
        # 顺手清掉过期的黑名单条目，表不会无限增长
        await session.execute(
            delete(RevokedToken).where(RevokedToken.expires_at < datetime.now(UTC))
        )
        await session.commit()
    if refresh_cookie:
        row = await session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_cookie))
        )
        if row and row.revoked_at is None:
            row.revoked_at = datetime.now(UTC)
            await session.commit()
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/v1/auth")
    response.delete_cookie("csrf_token", path="/")


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
