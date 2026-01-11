import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional

from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import DatabaseSystemException
from app.models import Workout, WorkoutExercise, Set, Exercise

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


def get_all_exercise_records(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """
    Returns personal bests for all exercises the user has performed.
    Includes exercise name, category, max weight, max reps at that weight, and date achieved.
    """
    try:
        # Subquery to get max weight per exercise
        max_weight_subq = (
            select(
                WorkoutExercise.exercise_id,
                func.max(Set.weight).label("max_weight")
            )
            .join(Set, WorkoutExercise.id == Set.workout_exercise_id)
            .join(Workout, WorkoutExercise.workout_id == Workout.id)
            .where(Workout.user_id == user_id)
            .where(Set.weight > 0)
            .group_by(WorkoutExercise.exercise_id)
            .subquery()
        )

        # Main query to get exercise details along with the PB info
        stmt = (
            select(
                Exercise.id,
                Exercise.name,
                Exercise.category,
                max_weight_subq.c.max_weight,
                Workout.date,
                Set.reps
            )
            .join(max_weight_subq, Exercise.id == max_weight_subq.c.exercise_id)
            .join(WorkoutExercise, and_(
                WorkoutExercise.exercise_id == Exercise.id,
            ))
            .join(Set, and_(
                Set.workout_exercise_id == WorkoutExercise.id,
                Set.weight == max_weight_subq.c.max_weight
            ))
            .join(Workout, and_(
                WorkoutExercise.workout_id == Workout.id,
                Workout.user_id == user_id
            ))
            .order_by(Exercise.name)
        )

        results = db.execute(stmt).all()

        # Deduplicate by exercise_id, keeping the one with most reps at max weight
        records_dict = {}
        for row in results:
            ex_id = row.id
            if ex_id not in records_dict or row.reps > records_dict[ex_id]["reps"]:
                records_dict[ex_id] = {
                    "exercise_id": row.id,
                    "exercise_name": row.name,
                    "category": row.category,
                    "max_weight": row.max_weight,
                    "reps": row.reps,
                    "date_achieved": str(row.date)
                }

        return list(records_dict.values())

    except SQLAlchemyError as e:
        logger.error(f"DB Error fetching all records: {e}")
        raise DatabaseSystemException(str(e))


def get_exercise_history(
    db: Session,
    user_id: int,
    exercise_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Returns full set history for an exercise with optional date filtering.
    Each entry includes workout date, set details (weight, reps, rpe).
    """
    try:
        stmt = (
            select(
                Workout.id.label("workout_id"),
                Workout.date,
                Workout.name.label("workout_name"),
                Set.order,
                Set.weight,
                Set.reps,
                Set.rpe
            )
            .join(WorkoutExercise, Workout.id == WorkoutExercise.workout_id)
            .join(Set, WorkoutExercise.id == Set.workout_exercise_id)
            .where(Workout.user_id == user_id)
            .where(WorkoutExercise.exercise_id == exercise_id)
        )

        if start_date:
            stmt = stmt.where(Workout.date >= start_date)
        if end_date:
            stmt = stmt.where(Workout.date <= end_date)

        stmt = stmt.order_by(desc(Workout.date), Set.order).limit(limit)

        results = db.execute(stmt).all()

        return [
            {
                "workout_id": row.workout_id,
                "date": str(row.date),
                "workout_name": row.workout_name,
                "set_order": row.order,
                "weight": row.weight,
                "reps": row.reps,
                "rpe": row.rpe
            }
            for row in results
        ]

    except SQLAlchemyError as e:
        logger.error(f"DB Error fetching exercise history: {e}")
        raise DatabaseSystemException(str(e))


def get_previous_lift(db: Session, user_id: int, exercise_id: int) -> Optional[Dict[str, Any]]:
    """
    Returns the most recent performance for an exercise (last workout where it was performed).
    """
    try:
        # Get the most recent workout containing this exercise
        stmt = (
            select(
                Workout.id,
                Workout.date,
                Workout.name
            )
            .join(WorkoutExercise, Workout.id == WorkoutExercise.workout_id)
            .where(Workout.user_id == user_id)
            .where(WorkoutExercise.exercise_id == exercise_id)
            .order_by(desc(Workout.date))
            .limit(1)
        )

        workout_result = db.execute(stmt).first()
        if not workout_result:
            return None

        # Get all sets from that workout for this exercise
        sets_stmt = (
            select(Set.order, Set.weight, Set.reps, Set.rpe)
            .join(WorkoutExercise, Set.workout_exercise_id == WorkoutExercise.id)
            .where(WorkoutExercise.workout_id == workout_result.id)
            .where(WorkoutExercise.exercise_id == exercise_id)
            .order_by(Set.order)
        )

        sets_result = db.execute(sets_stmt).all()

        return {
            "workout_id": workout_result.id,
            "date": str(workout_result.date),
            "workout_name": workout_result.name,
            "sets": [
                {
                    "order": s.order,
                    "weight": s.weight,
                    "reps": s.reps,
                    "rpe": s.rpe
                }
                for s in sets_result
            ]
        }

    except SQLAlchemyError as e:
        logger.error(f"DB Error fetching previous lift: {e}")
        raise DatabaseSystemException(str(e))


def get_record_history(
    db: Session,
    user_id: int,
    exercise_id: int,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Returns the history of personal records for an exercise.
    Shows when each new PR was achieved over time.
    """
    try:
        # Get all sessions for this exercise ordered by date
        stmt = (
            select(
                Workout.date,
                func.max(Set.weight).label("max_weight"),
                func.max(Set.reps).label("max_reps_at_weight")
            )
            .join(WorkoutExercise, Workout.id == WorkoutExercise.workout_id)
            .join(Set, WorkoutExercise.id == Set.workout_exercise_id)
            .where(Workout.user_id == user_id)
            .where(WorkoutExercise.exercise_id == exercise_id)
            .where(Set.weight > 0)
            .group_by(Workout.id, Workout.date)
            .order_by(asc(Workout.date))
        )

        results = db.execute(stmt).all()

        # Track running max to identify when PRs were set
        records = []
        running_max = 0.0

        for row in results:
            if row.max_weight > running_max:
                running_max = row.max_weight
                records.append({
                    "date": str(row.date),
                    "weight": row.max_weight,
                    "is_current_pr": False
                })

        # Mark the most recent as current PR
        if records:
            records[-1]["is_current_pr"] = True

        return records[-limit:]  # Return most recent PRs

    except SQLAlchemyError as e:
        logger.error(f"DB Error fetching record history: {e}")
        raise DatabaseSystemException(str(e))


def get_workout_history(
    db: Session,
    user_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    exercise_id: Optional[int] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Returns workout history with optional filters.
    Includes total volume, exercise count, and summary.
    """
    try:
        # Base query for workouts
        stmt = (
            select(Workout)
            .where(Workout.user_id == user_id)
            .options(
                selectinload(Workout.exercises).selectinload(WorkoutExercise.exercise_catalog),
                selectinload(Workout.exercises).selectinload(WorkoutExercise.sets)
            )
        )

        if start_date:
            stmt = stmt.where(Workout.date >= start_date)
        if end_date:
            stmt = stmt.where(Workout.date <= end_date)

        # If filtering by exercise or category, we need to join
        if exercise_id or category:
            stmt = stmt.join(WorkoutExercise, Workout.id == WorkoutExercise.workout_id)
            if exercise_id:
                stmt = stmt.where(WorkoutExercise.exercise_id == exercise_id)
            if category:
                stmt = stmt.join(Exercise, WorkoutExercise.exercise_id == Exercise.id)
                stmt = stmt.where(Exercise.category == category)
            stmt = stmt.distinct()

        # Count total before pagination
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = db.scalar(count_stmt) or 0

        # Apply pagination
        stmt = stmt.order_by(desc(Workout.date)).offset(offset).limit(limit)

        workouts = db.scalars(stmt).all()

        # Format results
        workout_list = []
        for workout in workouts:
            total_volume = 0
            total_sets = 0
            exercises_summary = []

            for we in workout.exercises:
                exercise_volume = sum(s.weight * s.reps for s in we.sets)
                total_volume += exercise_volume
                total_sets += len(we.sets)
                exercises_summary.append({
                    "exercise_id": we.exercise_id,
                    "exercise_name": we.exercise_catalog.name if we.exercise_catalog else "Unknown",
                    "category": we.exercise_catalog.category if we.exercise_catalog else None,
                    "sets_count": len(we.sets),
                    "top_weight": max((s.weight for s in we.sets), default=0)
                })

            workout_list.append({
                "id": workout.id,
                "name": workout.name,
                "date": str(workout.date),
                "notes": workout.notes,
                "total_volume": total_volume,
                "total_sets": total_sets,
                "exercises_count": len(workout.exercises),
                "exercises": exercises_summary
            })

        return {
            "total": total_count,
            "workouts": workout_list
        }

    except SQLAlchemyError as e:
        logger.error(f"DB Error fetching workout history: {e}")
        raise DatabaseSystemException(str(e))


def get_volume_over_time(
    db: Session,
    user_id: int,
    days: int = 30,
    exercise_id: Optional[int] = None,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Returns daily volume data for charting.
    """
    try:
        start_date = datetime.now().date() - timedelta(days=days)

        stmt = (
            select(
                Workout.date,
                func.sum(Set.weight * Set.reps).label("volume")
            )
            .join(WorkoutExercise, Workout.id == WorkoutExercise.workout_id)
            .join(Set, WorkoutExercise.id == Set.workout_exercise_id)
            .where(Workout.user_id == user_id)
            .where(Workout.date >= start_date)
        )

        if exercise_id:
            stmt = stmt.where(WorkoutExercise.exercise_id == exercise_id)
        if category:
            stmt = stmt.join(Exercise, WorkoutExercise.exercise_id == Exercise.id)
            stmt = stmt.where(Exercise.category == category)

        stmt = stmt.group_by(Workout.date).order_by(asc(Workout.date))

        results = db.execute(stmt).all()

        return [
            {"date": str(row.date), "volume": float(row.volume or 0)}
            for row in results
        ]

    except SQLAlchemyError as e:
        logger.error(f"DB Error fetching volume over time: {e}")
        raise DatabaseSystemException(str(e))


def get_stats_summary(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Returns overall stats summary for the user.
    """
    try:
        # Total workouts
        total_workouts = db.scalar(
            select(func.count(Workout.id)).where(Workout.user_id == user_id)
        ) or 0

        # Total volume lifted all time
        total_volume = db.scalar(
            select(func.sum(Set.weight * Set.reps))
            .join(WorkoutExercise, Set.workout_exercise_id == WorkoutExercise.id)
            .join(Workout, WorkoutExercise.workout_id == Workout.id)
            .where(Workout.user_id == user_id)
        ) or 0

        # Total sets
        total_sets = db.scalar(
            select(func.count(Set.id))
            .join(WorkoutExercise, Set.workout_exercise_id == WorkoutExercise.id)
            .join(Workout, WorkoutExercise.workout_id == Workout.id)
            .where(Workout.user_id == user_id)
        ) or 0

        # Unique exercises performed
        unique_exercises = db.scalar(
            select(func.count(func.distinct(WorkoutExercise.exercise_id)))
            .join(Workout, WorkoutExercise.workout_id == Workout.id)
            .where(Workout.user_id == user_id)
        ) or 0

        # Current streak (consecutive days with workouts ending today or yesterday)
        today = datetime.now().date()
        streak = 0
        check_date = today

        while True:
            has_workout = db.scalar(
                select(func.count(Workout.id))
                .where(Workout.user_id == user_id)
                .where(Workout.date == check_date)
            )
            if has_workout and has_workout > 0:
                streak += 1
                check_date -= timedelta(days=1)
            elif check_date == today:
                # Allow for today not having a workout yet, check yesterday
                check_date -= timedelta(days=1)
            else:
                break

        # This month workouts
        first_of_month = today.replace(day=1)
        this_month_workouts = db.scalar(
            select(func.count(Workout.id))
            .where(Workout.user_id == user_id)
            .where(Workout.date >= first_of_month)
        ) or 0

        return {
            "total_workouts": total_workouts,
            "total_volume": float(total_volume),
            "total_sets": total_sets,
            "unique_exercises": unique_exercises,
            "current_streak": streak,
            "this_month_workouts": this_month_workouts
        }

    except SQLAlchemyError as e:
        logger.error(f"DB Error fetching stats summary: {e}")
        raise DatabaseSystemException(str(e))
