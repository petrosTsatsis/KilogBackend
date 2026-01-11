"""seed_exercises

Revision ID: 9b4c6d8e0f2a
Revises: 8a3b5c7d9e1f
Create Date: 2026-01-08 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b4c6d8e0f2a'
down_revision: Union[str, Sequence[str], None] = '8a3b5c7d9e1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# System exercises (user_id = NULL means available to all users)
EXERCISES = [
    # Push exercises
    {"name": "Bench Press", "category": "Push"},
    {"name": "Incline Bench Press", "category": "Push"},
    {"name": "Decline Bench Press", "category": "Push"},
    {"name": "Dumbbell Bench Press", "category": "Push"},
    {"name": "Incline Dumbbell Press", "category": "Push"},
    {"name": "Overhead Press", "category": "Push"},
    {"name": "Dumbbell Shoulder Press", "category": "Push"},
    {"name": "Arnold Press", "category": "Push"},
    {"name": "Push-ups", "category": "Push"},
    {"name": "Dips", "category": "Push"},
    {"name": "Cable Flyes", "category": "Push"},
    {"name": "Pec Deck", "category": "Push"},
    {"name": "Tricep Pushdown", "category": "Push"},
    {"name": "Skull Crushers", "category": "Push"},
    {"name": "Overhead Tricep Extension", "category": "Push"},
    {"name": "Lateral Raises", "category": "Push"},
    {"name": "Front Raises", "category": "Push"},

    # Pull exercises
    {"name": "Deadlift", "category": "Pull"},
    {"name": "Pull-ups", "category": "Pull"},
    {"name": "Chin-ups", "category": "Pull"},
    {"name": "Lat Pulldown", "category": "Pull"},
    {"name": "Barbell Row", "category": "Pull"},
    {"name": "Dumbbell Row", "category": "Pull"},
    {"name": "Cable Row", "category": "Pull"},
    {"name": "T-Bar Row", "category": "Pull"},
    {"name": "Face Pulls", "category": "Pull"},
    {"name": "Rear Delt Flyes", "category": "Pull"},
    {"name": "Shrugs", "category": "Pull"},
    {"name": "Barbell Curl", "category": "Pull"},
    {"name": "Dumbbell Curl", "category": "Pull"},
    {"name": "Hammer Curl", "category": "Pull"},
    {"name": "Preacher Curl", "category": "Pull"},
    {"name": "Cable Curl", "category": "Pull"},

    # Legs exercises
    {"name": "Squat", "category": "Legs"},
    {"name": "Front Squat", "category": "Legs"},
    {"name": "Leg Press", "category": "Legs"},
    {"name": "Hack Squat", "category": "Legs"},
    {"name": "Lunges", "category": "Legs"},
    {"name": "Bulgarian Split Squat", "category": "Legs"},
    {"name": "Romanian Deadlift", "category": "Legs"},
    {"name": "Stiff Leg Deadlift", "category": "Legs"},
    {"name": "Leg Curl", "category": "Legs"},
    {"name": "Leg Extension", "category": "Legs"},
    {"name": "Calf Raises", "category": "Legs"},
    {"name": "Seated Calf Raises", "category": "Legs"},
    {"name": "Hip Thrust", "category": "Legs"},
    {"name": "Glute Bridge", "category": "Legs"},
    {"name": "Good Mornings", "category": "Legs"},

    # Core exercises
    {"name": "Plank", "category": "Core"},
    {"name": "Side Plank", "category": "Core"},
    {"name": "Crunches", "category": "Core"},
    {"name": "Sit-ups", "category": "Core"},
    {"name": "Leg Raises", "category": "Core"},
    {"name": "Hanging Leg Raises", "category": "Core"},
    {"name": "Russian Twists", "category": "Core"},
    {"name": "Cable Woodchops", "category": "Core"},
    {"name": "Ab Wheel Rollout", "category": "Core"},
    {"name": "Dead Bug", "category": "Core"},
    {"name": "Bird Dog", "category": "Core"},
    {"name": "Mountain Climbers", "category": "Core"},

    # Cardio exercises
    {"name": "Running", "category": "Cardio"},
    {"name": "Cycling", "category": "Cardio"},
    {"name": "Rowing", "category": "Cardio"},
    {"name": "Elliptical", "category": "Cardio"},
    {"name": "Stair Climber", "category": "Cardio"},
    {"name": "Jump Rope", "category": "Cardio"},
    {"name": "Swimming", "category": "Cardio"},
    {"name": "Walking", "category": "Cardio"},
    {"name": "HIIT", "category": "Cardio"},
    {"name": "Burpees", "category": "Cardio"},
]


def upgrade() -> None:
    """Seed system exercises."""
    exercises_table = sa.table(
        'exercises',
        sa.column('name', sa.String),
        sa.column('category', sa.String),
        sa.column('user_id', sa.Integer),
    )

    op.bulk_insert(
        exercises_table,
        [{"name": ex["name"], "category": ex["category"], "user_id": None} for ex in EXERCISES]
    )


def downgrade() -> None:
    """Remove seeded system exercises."""
    op.execute("DELETE FROM exercises WHERE user_id IS NULL")
