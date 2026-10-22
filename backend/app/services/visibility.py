"""可见性规则：只有标记为公开的讨论才允许未登录访客查看。"""
from sqlalchemy.sql import ColumnElement, true

from app.models import Discussion, User


def discussion_visible(user: User | None) -> ColumnElement:
    if user is not None:
        return true()
    return Discussion.is_public.is_(True)


def can_view(discussion: Discussion, user: User | None) -> bool:
    return discussion.is_public or user is not None
