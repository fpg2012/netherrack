from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Notification(Base):
    """回复 / 引用 / 最佳回复 / 系统通知。

    同一收件人、同一类型、同一帖子只记一条（唯一约束 + ON CONFLICT DO NOTHING）。
    """

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    kind: Mapped[str] = mapped_column(String(24))
    # 系统通知没有对应的讨论/帖子
    discussion_id: Mapped[int | None] = mapped_column(
        ForeignKey("discussions.id", ondelete="CASCADE"), index=True
    )
    post_id: Mapped[int | None] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    # 仅系统通知使用：标题和正文（纯文本，保留换行）
    title: Mapped[str | None] = mapped_column(String(120))
    body: Mapped[str | None] = mapped_column(Text)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    actor = relationship("User", foreign_keys=[actor_id], lazy="joined")

    __table_args__ = (
        UniqueConstraint("recipient_id", "kind", "post_id", name="uq_notification"),
    )
