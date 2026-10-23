import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class RegisterIn(BaseModel):
    code: str = Field(min_length=8, max_length=64)
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=10, max_length=256)
    nickname: str | None = Field(default=None, max_length=64)

    @field_validator("username")
    @classmethod
    def _strip_username(cls, value: str) -> str:
        return value.strip()

    @field_validator("email")
    @classmethod
    def _check_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("邮箱格式不正确")
        return value

    @field_validator("nickname")
    @classmethod
    def _strip_nickname(cls, value: str | None) -> str | None:
        value = (value or "").strip()
        return value or None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str | None = None
    avatar_path: str | None = None
    bio: str | None = None
    is_admin: bool = False


class LoginOut(BaseModel):
    user: UserOut
    csrf_token: str
