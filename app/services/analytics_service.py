import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import DatabaseSystemException
from app.models import Workout, WorkoutExercise, Set

logger = logging.getLogger(__name__)


def get_personal_best(db: Session, user_id: int, exercise_id: int) -> Optional[float]:
    """
    Returns the maximum weight ever lifted for a specific exercise by the user.
    """
    try:
        stmt = (
            select(func.max(Set.weight))
            .join(WorkoutExercise, Set.workout_exercise_id == WorkoutExercise.id)
            .join(Workout, WorkoutExercise.workout_id == Workout.id)
            .where(Workout.user_id == user_id)
            .where(WorkoutExercise.exercise_id == exercise_id)
        )
        # Returns None if no history exists
        return db.scalar(stmt)
    except SQLAlchemyError as e:
        logger.error(f"DB Error calculating PB: {e}")
        raise DatabaseSystemException(str(e))


def get_exercise_progress(db: Session, user_id: int, exercise_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Returns data points for a chart: Date vs Max Weight for that session.
    Ordered by date ascending (oldest to newest).
    """
    try:
        # We want: Date, Max(Weight)
        # Grouped by Workout
        stmt = (
            select(Workout.date, func.max(Set.weight).label("top_weight"))
            .join(WorkoutExercise, Workout.exercises)  # Magic of relationships
            .join(Set, WorkoutExercise.sets)
            .where(Workout.user_id == user_id)
            .where(WorkoutExercise.exercise_id == exercise_id)
            .group_by(Workout.id, Workout.date)
            .order_by(Workout.date.asc())
            .limit(limit)
        )

        results = db.execute(stmt).all()

        # Convert to clean list of dicts for the API
        return [
            {"date": row.date, "weight": row.top_weight}
            for row in results
        ]

    except SQLAlchemyError as e:
        logger.error(f"DB Error fetching progress: {e}")
        raise DatabaseSystemException(str(e))


def get_weekly_consistency(db: Session, user_id: int) -> int:
    """
    Returns the number of workouts completed in the last 7 days.
    """
    try:
        seven_days_ago = datetime.now().date() - timedelta(days=7)

        stmt = (
            select(func.count(Workout.id))
            .where(Workout.user_id == user_id)
            .where(Workout.date >= seven_days_ago)
        )
        return db.scalar(stmt) or 0

    except SQLAlchemyError as e:
        logger.error(f"DB Error fetching consistency: {e}")
        raise DatabaseSystemException(str(e))
