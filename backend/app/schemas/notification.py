from datetime import datetime

from pydantic import BaseModel

from app.schemas.content import UserBrief


class NotificationOut(BaseModel):
    id: int
    kind: str
    discussion_id: int
    discussion_title: str
    post_id: int
    post_number: int | None = None
    actor: UserBrief | None = None
    read: bool = False
    created_at: datetime
