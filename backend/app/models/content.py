from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    color: Mapped[str | None] = mapped_column(String(16))
    is_qna: Mapped[bool] = mapped_column(Boolean, default=False)
    position: Mapped[int] = mapped_column(Integer, default=0)


class DiscussionTag(Base):
    __tablename__ = "discussion_tags"

    discussion_id: Mapped[int] = mapped_column(
        ForeignKey("discussions.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


class Discussion(Base):
    __tablename__ = "discussions"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    # 标题的分词结果，供全文检索使用（中文没有空格，simple 配置切不开）
    search_text: Mapped[str] = mapped_column(Text, default="", server_default="")
    title_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('simple', search_text)", persisted=True),
    )
    slug: Mapped[str | None] = mapped_column(String(255))
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    is_sticky: Mapped[bool] = mapped_column(Boolean, default=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    # 折叠：不在列表出现，且强制不公开
    is_collapsed: Mapped[bool] = mapped_column(Boolean, default=False)
    # 默认私密：只有显式标记为 public 的讨论才允许游客查看
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    post_count: Mapped[int] = mapped_column(Integer, default=0)
    best_answer_post_id: Mapped[int | None] = mapped_column(
        ForeignKey("posts.id", ondelete="SET NULL", use_alter=True, name="fk_best_answer"),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    author = relationship("User", lazy="joined")
    tags = relationship(
        "Tag", secondary="discussion_tags", lazy="selectin", order_by="Tag.position"
    )

    __table_args__ = (
        Index("ix_discussions_last_posted", "last_posted_at"),
        Index("ix_discussions_title_vector", "title_vector", postgresql_using="gin"),
    )


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    discussion_id: Mapped[int] = mapped_column(
        ForeignKey("discussions.id", ondelete="CASCADE"), index=True
    )
    number: Mapped[int] = mapped_column(Integer)
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    search_text: Mapped[str] = mapped_column(Text, default="", server_default="")
    # 由 search_text 自动生成，写入时不用手动同步
    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('simple', search_text)", persisted=True),
    )
    body_md: Mapped[str | None] = mapped_column(Text)      # 新帖子用 Markdown
    body_html: Mapped[str] = mapped_column(Text)           # 渲染 + 清洗后的 HTML
    is_legacy: Mapped[bool] = mapped_column(Boolean, default=False)
    # 楼层被折叠时正文不下发，前端只显示占位文字
    is_collapsed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    edited_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    hidden_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    author = relationship("User", foreign_keys=[author_id], lazy="joined")

    __table_args__ = (
        UniqueConstraint("discussion_id", "number", name="uq_post_number"),
        Index("ix_posts_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_posts_discussion_number", "discussion_id", "number"),
    )


class DiscussionEvent(Base):
    """改标题、改标签、置顶这类操作，不再混进 posts 表。"""

    __tablename__ = "discussion_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    discussion_id: Mapped[int] = mapped_column(
        ForeignKey("discussions.id", ondelete="CASCADE"), index=True
    )
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    kind: Mapped[str] = mapped_column(String(32))
    payload: Mapped[Any] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    actor = relationship("User", lazy="joined")


class Upload(Base):
    __tablename__ = "uploads"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    path: Mapped[str] = mapped_column(String(255))
    filename: Mapped[str] = mapped_column(String(255))
    size: Mapped[int] = mapped_column(BigInteger, default=0)
    mime: Mapped[str | None] = mapped_column(String(128))
    uploader_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
