"""discussion public flag

把 is_private 换成语义相反的 is_public：默认不公开，只有显式标记才给游客看。

Revision ID: 27971469fed1
Revises: fc0514ff27b2
Create Date: 2026-10-23 03:20:00
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "27971469fed1"
down_revision: str | None = "fc0514ff27b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("discussions", "is_private", new_column_name="is_public")
    # 迁移过来的内容一律先设为不公开，等管理员手动标记
    op.execute("UPDATE discussions SET is_public = false")
    op.alter_column("discussions", "is_public", server_default=sa.text("false"),
                    existing_type=sa.Boolean(), nullable=False)
    op.create_index("ix_discussions_is_public", "discussions", ["is_public"])


def downgrade() -> None:
    op.drop_index("ix_discussions_is_public", table_name="discussions")
    op.alter_column("discussions", "is_public", new_column_name="is_private")
    op.execute("UPDATE discussions SET is_private = NOT is_private")
