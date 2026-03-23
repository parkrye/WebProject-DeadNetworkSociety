"""add view_count, bio, avatar_url

Revision ID: c3a1b2d3e4f5
Revises: b2fead9b7a5b
Create Date: 2026-03-23 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3a1b2d3e4f5'
down_revision: Union[str, None] = 'b2fead9b7a5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('posts', sa.Column('view_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('bio', sa.String(length=200), server_default='', nullable=False))
    op.add_column('users', sa.Column('avatar_url', sa.String(length=500), server_default='', nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'bio')
    op.drop_column('posts', 'view_count')
