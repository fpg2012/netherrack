from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, SessionDep, verify_csrf
from app.core.config import settings
from app.core.ratelimit import limiter
from app.core.security import (
    create_token,
    decode_token,
    hash_password,
    hash_token,
    new_csrf_token,
    verify_password,
)
from app.models import Invite, RefreshToken, RevokedToken, User
from app.schemas.auth import LoginIn, LoginOut, RegisterIn, UserOut
from app.services.audit import audit
from app.services.invites import CODE_LEN, hash_code, normalize

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
@limiter.limit("10/minute")
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


@router.post("/register", response_model=LoginOut, status_code=201)
@limiter.limit("10/minute")
async def register(payload: RegisterIn, request: Request, response: Response,
                   session: SessionDep) -> LoginOut:
    """凭邀请码注册。邀请码一次性使用，整个流程在同一个事务里完成。"""
    code = normalize(payload.code)
    # 长度不对就不查库，也避免异常输入进入日志
    if len(code) != CODE_LEN:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "邀请码无效或已失效")
    invite = await session.scalar(
        select(Invite).where(Invite.code_hash == hash_code(code)).with_for_update()
    )
    now = datetime.now(UTC)
    if (invite is None or invite.used_at is not None or invite.revoked_at is not None
            or (invite.expires_at is not None and invite.expires_at < now)):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "邀请码无效或已失效")

    taken = await session.scalar(
        select(User.id).where(or_(
            func.lower(User.username) == payload.username.lower(),
            func.lower(User.email) == payload.email,
        ))
    )
    if taken is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "用户名或邮箱已被使用")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        nickname=payload.nickname,
        is_active=True,
        is_admin=False,
    )
    session.add(user)
    await session.flush()
    invite.used_by = user.id
    invite.used_at = now
    await audit(session, actor_id=user.id, action="user.register",
                target_type="user", target_id=user.id, invite_id=invite.id)
    try:
        await session.commit()
    except IntegrityError:                # 并发下唯一约束兜底
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "用户名或邮箱已被使用") from None

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
