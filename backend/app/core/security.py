"""密码哈希、JWT 与 CSRF。"""
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

from app.core.config import settings

_argon2 = PasswordHasher()


def hash_password(password: str) -> str:
    return _argon2.hash(password)


def verify_password(password: str, stored: str) -> tuple[bool, bool]:
    """返回 (是否正确, 是否需要重新哈希)。

    Flarum 的密码是 bcrypt($2y$)，登录成功后顺手升级成 argon2。
    """
    if stored.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            ok = bcrypt.checkpw(password.encode(), stored.encode())
        except ValueError:
            return False, False
        return ok, ok
    try:
        _argon2.verify(stored, password)
    except VerificationError:
        return False, False
    return True, _argon2.check_needs_rehash(stored)


def create_token(subject: str, token_type: str, ttl: int) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + timedelta(seconds=ttl),
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_type: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None
    if payload.get("type") != expected_type:
        return None
    return payload


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def csrf_matches(cookie_value: str | None, header_value: str | None) -> bool:
    if not cookie_value or not header_value:
        return False
    return hmac.compare_digest(cookie_value, header_value)


def hash_token(token: str) -> str:
    import hashlib

    return hashlib.sha256(token.encode()).hexdigest()
