"""add_workout_name

Revision ID: 8a3b5c7d9e1f
Revises: 4075bedb62ce
Create Date: 2026-01-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a3b5c7d9e1f'
down_revision: Union[str, Sequence[str], None] = '4075bedb62ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add name column to workouts table."""
    op.add_column('workouts', sa.Column('name', sa.String(255), nullable=True))


def downgrade() -> None:
    """Remove name column from workouts table."""
    op.drop_column('workouts', 'name')
