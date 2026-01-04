import logging
from typing import Sequence

from sqlalchemy import select, desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import (
    DatabaseSystemException,
    WorkoutNotFoundException,
    PermissionDeniedException,
    ExerciseNotFoundException
)
from app.models import Workout, WorkoutExercise, Set
from app.schemas import WorkoutUpdate
from app.schemas.workout_schema import WorkoutCreate
from app.services.exercise_service import get_exercise_by_id

logger = logging.getLogger(__name__)


def create_workout(db: Session, workout_in: WorkoutCreate, user_id: int) -> Workout:
    logger.info(f"Creating workout for user {user_id} on {workout_in.date}")

    try:
        # Create the Parent (Workout)
        # exclude={"exercises"} because we process them manually below
        workout_data = workout_in.model_dump(exclude={"exercises"})
        db_workout = Workout(**workout_data, user_id=user_id)
        db.add(db_workout)
        db.flush()  # Flush to generate db_workout.id

        # Iterate through Exercises
        if workout_in.exercises:
            for ex_data in workout_in.exercises:

                # Check if this user can use the specified exercise.
                # If they try to log a workout with someone else's private exercise, this raises.
                # We use the service function we wrote earlier to enforce this.
                try:
                    get_exercise_by_id(db, ex_data.exercise_id, user_id)
                except ExerciseNotFoundException:
                    logger.warning(f"User {user_id} tried to use invalid exercise {ex_data.exercise_id}")
                    raise ExerciseNotFoundException(ex_data.exercise_id)

                # Link Workout -> Exercise
                db_work_exercise = WorkoutExercise(
                    workout_id=db_workout.id,
                    exercise_id=ex_data.exercise_id
                )
                db.add(db_work_exercise)
                db.flush()  # Flush to generate db_work_exercise.id

                # Iterate through Sets
                if ex_data.sets:
                    for set_data in ex_data.sets:
                        db_set = Set(
                            workout_exercise_id=db_work_exercise.id,
                            **set_data.model_dump()
                        )
                        db.add(db_set)

        db.commit()
        db.refresh(db_workout)
        return db_workout

    except ExerciseNotFoundException:
        # Catch our custom validation error -> Rollback DB -> Re-raise for API
        db.rollback()
        raise

    except SQLAlchemyError as e:
        # Catch generic DB errors -> Rollback DB -> Raise System Exception
        db.rollback()
        logger.error(f"DB Error creating workout: {e}")
        raise DatabaseSystemException(str(e))


def get_workout_by_id(db: Session, workout_id: int, user_id: int) -> Workout:
    logger.debug(f"Getting workout '{workout_id}' for user {user_id}")
    try:
        stmt = (
            select(Workout)
            .where(Workout.id == workout_id)
            .options(
                selectinload(Workout.exercises).options(
                    selectinload(WorkoutExercise.exercise_catalog),  # Load "Bench Press" name
                    selectinload(WorkoutExercise.sets)  # Load "100kg x 5"
                )
            )
        )
        workout = db.scalar(stmt)

        if not workout:
            raise WorkoutNotFoundException(workout_id)

        # Users can only see their own workouts
        if workout.user_id != user_id:
            raise PermissionDeniedException("Workout belongs to another user", user_id)

        return workout

    except SQLAlchemyError as e:
        logger.error(f"DB Error fetching workout {workout_id}: {e}")
        raise DatabaseSystemException(str(e))


def list_user_workouts(
        db: Session,
        user_id: int,
        limit: int = 20,
        offset: int = 0
) -> Sequence[Workout]:
    """
    Returns workout history, ordered by date (newest first).
    """
    logger.debug(f"Listing workouts for user {user_id}, limit={limit}, offset={offset}")
    try:
        stmt = (
            select(Workout)
            .where(Workout.user_id == user_id)
            .order_by(desc(Workout.date))
            .limit(limit)
            .offset(offset)
            # We might want to load exercise names here for the summary card,
            # but usually the list view is simple.
            # skip it for now.
        )
        return db.scalars(stmt).all()

    except SQLAlchemyError as e:
        logger.error(f"DB Error listing workouts: {e}")
        raise DatabaseSystemException(str(e))


def update_workout(db: Session, workout_id: int, workout_in: WorkoutUpdate, user_id: int) -> Workout:
    logger.info(f"Updating workout {workout_id} for user {user_id}")

    # Fetch existing workout with permissions
    db_workout = get_workout_by_id(db, workout_id, user_id)

    try:
        # Update Basic Fields
        db_workout.date = workout_in.date
        db_workout.notes = workout_in.notes

        # Because we set cascade="all, delete-orphan" in the models,
        # removing the item from the list automagically deletes it from the DB.
        db_workout.exercises.clear()

        # Re-build the tree (Same logic as Create)
        if workout_in.exercises:
            for ex_data in workout_in.exercises:

                # Security Check
                try:
                    get_exercise_by_id(db, ex_data.exercise_id, user_id)
                except ExerciseNotFoundException:
                    raise ExerciseNotFoundException(ex_data.exercise_id)

                # Create Link
                new_work_exercise = WorkoutExercise(
                    exercise_id=ex_data.exercise_id
                    # We rely on SQLAlchemy to link this to db_workout automatically
                    # when we append it below.
                )

                # Create Sets
                if ex_data.sets:
                    for set_data in ex_data.sets:
                        new_set = Set(**set_data.model_dump())
                        new_work_exercise.sets.append(new_set)

                # Add to parent list
                db_workout.exercises.append(new_work_exercise)

        db.commit()
        db.refresh(db_workout)
        return db_workout

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"DB Error updating workout: {e}")
        raise DatabaseSystemException(str(e))


def delete_workout(db: Session, workout_id: int, user_id: int) -> None:
    logger.debug(f"Deleting workout {workout_id} for user {user_id}")
    workout = get_workout_by_id(db, workout_id, user_id)  # Reuse get logic for checks

    try:
        db.delete(workout)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseSystemException(str(e))
