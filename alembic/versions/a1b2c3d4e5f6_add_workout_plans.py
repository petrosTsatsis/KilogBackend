"""add_workout_plans

Revision ID: a1b2c3d4e5f6
Revises: 9b4c6d8e0f2a
Create Date: 2026-01-09 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '9b4c6d8e0f2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create workout_plans and workout_plan_days tables."""
    # Create workout_plans table
    op.create_table(
        'workout_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, server_default='My Workout Plan'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workout_plans_id'), 'workout_plans', ['id'], unique=False)

    # Create workout_plan_days table
    op.create_table(
        'workout_plan_days',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workout_plan_id', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('is_rest_day', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('workout_name', sa.String(255), nullable=True),
        sa.Column('exercises', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['workout_plan_id'], ['workout_plans.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workout_plan_days_id'), 'workout_plan_days', ['id'], unique=False)


def downgrade() -> None:
    """Drop workout_plan_days and workout_plans tables."""
    op.drop_index(op.f('ix_workout_plan_days_id'), table_name='workout_plan_days')
    op.drop_table('workout_plan_days')
    op.drop_index(op.f('ix_workout_plans_id'), table_name='workout_plans')
    op.drop_table('workout_plans')
