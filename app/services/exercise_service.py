import logging
from typing import Optional, Sequence

from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ExerciseNotFoundException,
    PermissionDeniedException,
    DatabaseSystemException
)
from app.models import Exercise
from app.schemas.exercise_schema import ExerciseCreate, ExerciseBase

logger = logging.getLogger(__name__)


def list_exercises(
        db: Session,
        user_id: int,
        search_query: Optional[str] = None,
        limit: int = 100
) -> Sequence[Exercise]:
    logger.debug(f"Listing exercises for user {user_id}")
    try:
        # Retrieve both System Exercises (user_id is null) and user's custom exercises
        stmt = select(Exercise).where(
            or_(
                Exercise.user_id == None,
                Exercise.user_id == user_id
            )
        )

        if search_query:
            # Case-insensitive search (ilike)
            # This will get enhanced with more advanced search later.
            stmt = stmt.where(Exercise.name.ilike(f"%{search_query}%"))

        stmt = stmt.limit(limit)

        return db.scalars(stmt).all()

    except SQLAlchemyError as e:
        logger.error(f"DB Error listing exercises: {e}")
        raise DatabaseSystemException(str(e))


def get_exercise_by_id(db: Session, exercise_id: int, user_id: int) -> Exercise:
    logger.debug(f"Getting exercise '{exercise_id}' by user {user_id}")
    try:
        stmt = select(Exercise).where(Exercise.id == exercise_id)
        exercise = db.scalar(stmt)

        if not exercise:
            raise ExerciseNotFoundException(exercise_id)

        # Permission Check: Is it private to ANOTHER user?
        if exercise.user_id is not None and exercise.user_id != user_id:
            # We throw NotFound instead of Forbidden to prevent enumeration attacks
            # (i.e. finding out how many exercises user 5 has)
            raise ExerciseNotFoundException(exercise_id)

        return exercise

    except SQLAlchemyError as e:
        logger.error(f"DB Error fetching exercise {exercise_id}: {e}")
        raise DatabaseSystemException(str(e))


def create_custom_exercise(db: Session, exercise_in: ExerciseCreate, user_id: int) -> Exercise:
    logger.info(f"Creating custom exercise '{exercise_in.name}' for user {user_id}")
    try:
        # We explicitly enforce the user_id here
        db_exercise = Exercise(
            **exercise_in.model_dump(),
            user_id=user_id
        )
        db.add(db_exercise)
        db.commit()
        db.refresh(db_exercise)
        return db_exercise

    except IntegrityError:
        db.rollback()
        # For now, we allow duplicate exercise names.
        # Later we will add a uniqueness constraint per user.
        raise DatabaseSystemException("Could not create exercise")

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"DB Error creating exercise: {e}")
        raise DatabaseSystemException(str(e))


def update_exercise(db: Session, exercise_id: int, exercise_in: ExerciseBase, user_id: int) -> Exercise:
    """
    Updates an exercise.
    Prerequisite: User must own the exercise.
    """
    stmt = select(Exercise).where(Exercise.id == exercise_id)
    exercise = db.scalar(stmt)

    if not exercise:
        raise ExerciseNotFoundException(exercise_id)

    # Cannot edit System Exercises
    if exercise.user_id is None:
        raise PermissionDeniedException("System Exercises", user_id)

    # Cannot edit other people's
    if exercise.user_id != user_id:
        raise PermissionDeniedException("Other User's Exercise", user_id)

    try:
        for key, value in exercise_in.model_dump(exclude_unset=True).items():
            setattr(exercise, key, value)

        db.commit()
        db.refresh(exercise)
        return exercise
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseSystemException(str(e))


def delete_exercise(db: Session, exercise_id: int, user_id: int) -> None:
    """
    Deletes an exercise.
    Prerequisite: User must own the exercise.
    """
    stmt = select(Exercise).where(Exercise.id == exercise_id)
    exercise = db.scalar(stmt)

    if not exercise:
        raise ExerciseNotFoundException(exercise_id)

    if exercise.user_id is None:
        raise PermissionDeniedException("System Exercises", user_id)

    if exercise.user_id != user_id:
        raise PermissionDeniedException("Other User's Exercise", user_id)

    try:
        db.delete(exercise)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseSystemException(str(e))
