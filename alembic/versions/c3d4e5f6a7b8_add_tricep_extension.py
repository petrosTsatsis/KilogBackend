"""add_tricep_extension

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-01-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Tricep Extension exercise."""
    exercises_table = sa.table(
        'exercises',
        sa.column('name', sa.String),
        sa.column('category', sa.String),
        sa.column('user_id', sa.Integer),
    )

    op.bulk_insert(
        exercises_table,
        [{"name": "Tricep Extension", "category": "Push", "user_id": None}]
    )


def downgrade() -> None:
    """Remove Tricep Extension exercise."""
    op.execute("DELETE FROM exercises WHERE name = 'Tricep Extension' AND user_id IS NULL")
