"""add_user_profiles

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create user_profiles table with enums."""
    # Create enums using raw SQL with IF NOT EXISTS equivalent
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE fitnessgoal AS ENUM (
                'LOSE_WEIGHT', 'BUILD_MUSCLE', 'GET_STRONGER', 'IMPROVE_ENDURANCE',
                'GENERAL_FITNESS', 'TONE_UP', 'BULK', 'CUT', 'ATHLETIC_PERFORMANCE', 'FLEXIBILITY'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE experiencelevel AS ENUM ('BEGINNER', 'INTERMEDIATE', 'ADVANCED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE equipmentaccess AS ENUM ('GYM', 'HOME', 'BODYWEIGHT');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create user_profiles table using existing enum types
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('primary_goal', postgresql.ENUM('LOSE_WEIGHT', 'BUILD_MUSCLE', 'GET_STRONGER', 'IMPROVE_ENDURANCE',
                  'GENERAL_FITNESS', 'TONE_UP', 'BULK', 'CUT', 'ATHLETIC_PERFORMANCE', 'FLEXIBILITY',
                  name='fitnessgoal', create_type=False), nullable=True),
        sa.Column('secondary_goals', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('training_days_per_week', sa.Integer(), nullable=True),
        sa.Column('experience_level', postgresql.ENUM('BEGINNER', 'INTERMEDIATE', 'ADVANCED',
                  name='experiencelevel', create_type=False), nullable=True),
        sa.Column('equipment_access', postgresql.ENUM('GYM', 'HOME', 'BODYWEIGHT',
                  name='equipmentaccess', create_type=False), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('weight_kg', sa.Float(), nullable=True),
        sa.Column('height_cm', sa.Float(), nullable=True),
        sa.Column('onboarding_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('onboarding_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_profiles_id'), 'user_profiles', ['id'], unique=False)
    op.create_index(op.f('ix_user_profiles_user_id'), 'user_profiles', ['user_id'], unique=True)


def downgrade() -> None:
    """Drop user_profiles table and enums."""
    op.drop_index(op.f('ix_user_profiles_user_id'), table_name='user_profiles')
    op.drop_index(op.f('ix_user_profiles_id'), table_name='user_profiles')
    op.drop_table('user_profiles')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS fitnessgoal')
    op.execute('DROP TYPE IF EXISTS experiencelevel')
    op.execute('DROP TYPE IF EXISTS equipmentaccess')
