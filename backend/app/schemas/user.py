from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str | None = None
    avatar_path: str | None = None
    joined_at: datetime
    is_admin: bool = False
    is_active: bool = True
    posts: int = 0
    discussions: int = 0


class UserProfile(UserListItem):
    bio: str | None = None


class UserPostItem(BaseModel):
    post_id: int
    discussion_id: int
    discussion_title: str
    number: int
    created_at: datetime
    snippet: str


class ProfileUpdate(BaseModel):
    nickname: str | None = None
    bio: str | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class AdminPasswordReset(BaseModel):
    # 不传则自动生成随机临时密码
    new_password: str | None = Field(default=None, min_length=8, max_length=128)


class PasswordResetOut(BaseModel):
    password: str


class UserStatusUpdate(BaseModel):
    is_active: bool
