"""add follows table

Revision ID: 485122d2a1fe
Revises: 65126465f6ae
Create Date: 2026-03-23 16:21:22.481707
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '485122d2a1fe'
down_revision: Union[str, None] = '65126465f6ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('follows',
        sa.Column('follower_id', sa.Uuid(), nullable=False),
        sa.Column('following_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['follower_id'], ['users.id']),
        sa.ForeignKeyConstraint(['following_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('follower_id', 'following_id', name='uq_follow_pair'),
    )
    op.create_index('ix_follows_follower_id', 'follows', ['follower_id'])
    op.create_index('ix_follows_following_id', 'follows', ['following_id'])


def downgrade() -> None:
    op.drop_index('ix_follows_following_id', table_name='follows')
    op.drop_index('ix_follows_follower_id', table_name='follows')
    op.drop_table('follows')
