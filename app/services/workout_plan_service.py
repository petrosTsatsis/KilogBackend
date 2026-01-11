import logging
from datetime import date
from typing import Sequence, Optional

from sqlalchemy import select, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import (
    DatabaseSystemException,
    ResourceNotFoundException,
    PermissionDeniedException
)
from app.models import WorkoutPlan, WorkoutPlanDay
from app.schemas.workout_plan_schema import (
    WorkoutPlanCreate, WorkoutPlanUpdate, TodayPlanResponse, PlannedExercise
)

logger = logging.getLogger(__name__)


class WorkoutPlanNotFoundException(ResourceNotFoundException):
    def __init__(self, plan_id: int):
        super().__init__(resource="WorkoutPlan", id=plan_id)


def create_workout_plan(db: Session, plan_in: WorkoutPlanCreate, user_id: int) -> WorkoutPlan:
    """Create a new workout plan for a user."""
    logger.info(f"Creating workout plan '{plan_in.name}' for user {user_id}")

    try:
        # If this plan should be active, deactivate all other plans first
        if plan_in.is_active:
            _deactivate_all_plans(db, user_id)

        # Create the plan
        db_plan = WorkoutPlan(
            user_id=user_id,
            name=plan_in.name,
            is_active=plan_in.is_active
        )
        db.add(db_plan)
        db.flush()

        # Add days
        for day_data in plan_in.days:
            exercises_json = None
            if day_data.exercises:
                exercises_json = [ex.model_dump() for ex in day_data.exercises]

            db_day = WorkoutPlanDay(
                workout_plan_id=db_plan.id,
                day_of_week=day_data.day_of_week,
                is_rest_day=day_data.is_rest_day,
                workout_name=day_data.workout_name,
                exercises=exercises_json
            )
            db.add(db_day)

        db.commit()
        db.refresh(db_plan)
        return db_plan

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"DB Error creating workout plan: {e}")
        raise DatabaseSystemException(str(e))


def get_workout_plan_by_id(db: Session, plan_id: int, user_id: int) -> WorkoutPlan:
    """Get a workout plan by ID, ensuring user ownership."""
    logger.debug(f"Getting workout plan {plan_id} for user {user_id}")

    try:
        stmt = (
            select(WorkoutPlan)
            .where(WorkoutPlan.id == plan_id)
            .options(selectinload(WorkoutPlan.days))
        )
        plan = db.scalar(stmt)

        if not plan:
            raise WorkoutPlanNotFoundException(plan_id)

        if plan.user_id != user_id:
            raise PermissionDeniedException("WorkoutPlan", user_id)

        return plan

    except SQLAlchemyError as e:
        logger.error(f"DB Error fetching workout plan {plan_id}: {e}")
        raise DatabaseSystemException(str(e))


def list_user_workout_plans(db: Session, user_id: int) -> Sequence[WorkoutPlan]:
    """List all workout plans for a user."""
    logger.debug(f"Listing workout plans for user {user_id}")

    try:
        stmt = (
            select(WorkoutPlan)
            .where(WorkoutPlan.user_id == user_id)
            .options(selectinload(WorkoutPlan.days))
            .order_by(WorkoutPlan.created_at.desc())
        )
        return db.scalars(stmt).all()

    except SQLAlchemyError as e:
        logger.error(f"DB Error listing workout plans: {e}")
        raise DatabaseSystemException(str(e))


def get_active_plan(db: Session, user_id: int) -> Optional[WorkoutPlan]:
    """Get the user's currently active workout plan."""
    logger.debug(f"Getting active workout plan for user {user_id}")

    try:
        stmt = (
            select(WorkoutPlan)
            .where(and_(
                WorkoutPlan.user_id == user_id,
                WorkoutPlan.is_active == True
            ))
            .options(selectinload(WorkoutPlan.days))
        )
        return db.scalar(stmt)

    except SQLAlchemyError as e:
        logger.error(f"DB Error fetching active workout plan: {e}")
        raise DatabaseSystemException(str(e))


def update_workout_plan(db: Session, plan_id: int, plan_in: WorkoutPlanUpdate, user_id: int) -> WorkoutPlan:
    """Update a workout plan."""
    logger.info(f"Updating workout plan {plan_id} for user {user_id}")

    db_plan = get_workout_plan_by_id(db, plan_id, user_id)

    try:
        # Update basic fields
        if plan_in.name is not None:
            db_plan.name = plan_in.name

        # Handle active status
        if plan_in.is_active is not None:
            if plan_in.is_active and not db_plan.is_active:
                # Deactivate other plans first
                _deactivate_all_plans(db, user_id)
            db_plan.is_active = plan_in.is_active

        # Update days if provided
        if plan_in.days is not None:
            # Clear existing days
            db_plan.days.clear()

            # Add new days
            for day_data in plan_in.days:
                exercises_json = None
                if day_data.exercises:
                    exercises_json = [ex.model_dump() for ex in day_data.exercises]

                db_day = WorkoutPlanDay(
                    day_of_week=day_data.day_of_week,
                    is_rest_day=day_data.is_rest_day,
                    workout_name=day_data.workout_name,
                    exercises=exercises_json
                )
                db_plan.days.append(db_day)

        db.commit()
        db.refresh(db_plan)
        return db_plan

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"DB Error updating workout plan: {e}")
        raise DatabaseSystemException(str(e))


def delete_workout_plan(db: Session, plan_id: int, user_id: int) -> None:
    """Delete a workout plan."""
    logger.debug(f"Deleting workout plan {plan_id} for user {user_id}")

    db_plan = get_workout_plan_by_id(db, plan_id, user_id)

    try:
        db.delete(db_plan)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseSystemException(str(e))


def set_plan_active(db: Session, plan_id: int, user_id: int) -> WorkoutPlan:
    """Set a workout plan as the active plan."""
    logger.info(f"Setting workout plan {plan_id} as active for user {user_id}")

    db_plan = get_workout_plan_by_id(db, plan_id, user_id)

    try:
        # Deactivate all other plans
        _deactivate_all_plans(db, user_id)

        # Activate this plan
        db_plan.is_active = True
        db.commit()
        db.refresh(db_plan)
        return db_plan

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"DB Error setting active plan: {e}")
        raise DatabaseSystemException(str(e))


def get_today_plan(db: Session, user_id: int) -> TodayPlanResponse:
    """Get the planned workout for today based on the active plan."""
    logger.debug(f"Getting today's plan for user {user_id}")

    active_plan = get_active_plan(db, user_id)

    if not active_plan:
        return TodayPlanResponse(has_plan=False)

    # Get today's day of week (Python: Monday=0, Sunday=6)
    today_dow = date.today().weekday()

    # Find today's workout in the plan
    today_workout = None
    for day in active_plan.days:
        if day.day_of_week == today_dow:
            today_workout = day
            break

    if not today_workout:
        return TodayPlanResponse(
            has_plan=True,
            is_rest_day=True,
            plan_name=active_plan.name
        )

    if today_workout.is_rest_day:
        return TodayPlanResponse(
            has_plan=True,
            is_rest_day=True,
            plan_name=active_plan.name
        )

    # Parse exercises from JSON
    exercises = None
    if today_workout.exercises:
        exercises = [PlannedExercise(**ex) for ex in today_workout.exercises]

    return TodayPlanResponse(
        has_plan=True,
        is_rest_day=False,
        workout_name=today_workout.workout_name,
        exercises=exercises,
        plan_name=active_plan.name
    )


def _deactivate_all_plans(db: Session, user_id: int) -> None:
    """Helper to deactivate all plans for a user."""
    stmt = (
        select(WorkoutPlan)
        .where(and_(
            WorkoutPlan.user_id == user_id,
            WorkoutPlan.is_active == True
        ))
    )
    active_plans = db.scalars(stmt).all()
    for plan in active_plans:
        plan.is_active = False
