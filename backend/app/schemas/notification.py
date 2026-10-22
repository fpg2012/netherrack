from datetime import datetime

from pydantic import BaseModel

from app.schemas.content import UserBrief


class NotificationOut(BaseModel):
    id: int
    kind: str
    discussion_id: int | None = None
    discussion_title: str | None = None
    post_id: int | None = None
    post_number: int | None = None
    title: str | None = None
    body: str | None = None
    actor: UserBrief | None = None
    read: bool = False
    created_at: datetime


class NoticeIn(BaseModel):
    title: str
    body: str
