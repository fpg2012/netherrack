"""checkins

Revision ID: c4e5f6a7b8c9
Revises: 3ac3d618dc5e
Create Date: 2026-10-25 12:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = 'c4e5f6a7b8c9'
down_revision: str | None = '3ac3d618dc5e'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'checkins',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('checked_on', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'checked_on', name='uq_checkins_user_day'),
    )
    op.create_index(op.f('ix_checkins_user_id'), 'checkins', ['user_id'], unique=False)
    op.create_index(op.f('ix_checkins_checked_on'), 'checkins', ['checked_on'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_checkins_checked_on'), table_name='checkins')
    op.drop_index(op.f('ix_checkins_user_id'), table_name='checkins')
    op.drop_table('checkins')
