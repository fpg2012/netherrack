from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str | None = None
    avatar_path: str | None = None


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    color: str | None = None
    is_qna: bool = False


class TagWithCount(TagOut):
    count: int = 0


class DiscussionBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str | None = None
    is_sticky: bool = False
    is_locked: bool = False
    is_public: bool = False
    is_collapsed: bool = False
    post_count: int = 0
    created_at: datetime
    last_posted_at: datetime | None = None
    author: UserBrief | None = None
    tags: list[TagOut] = []


class DiscussionDetail(DiscussionBrief):
    best_answer_post_id: int | None = None


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: int
    created_at: datetime
    edited_at: datetime | None = None
    body_html: str
    body_md: str | None = None
    is_legacy: bool = False
    is_collapsed: bool = False
    author: UserBrief | None = None


class EventOut(BaseModel):
    id: int
    kind: str
    text: str
    created_at: datetime


class TimelineItem(BaseModel):
    """时间线里既有帖子也有操作记录，用 type 区分。"""

    type: str  # "post" | "event"
    id: int
    created_at: datetime
    post: PostOut | None = None
    event: EventOut | None = None


class SearchHit(BaseModel):
    post_id: int
    discussion_id: int
    discussion_title: str
    number: int
    created_at: datetime
    author: UserBrief | None = None
    snippet: str
