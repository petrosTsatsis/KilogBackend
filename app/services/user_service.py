import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import DatabaseSystemException, UserAlreadyExistsException, UserNotFoundException
from app.models import User, Workout, WorkoutExercise
from app.schemas import UserCreate, UserUpdate

logger = logging.getLogger(__name__)


def create_user(db: Session, user_in: UserCreate) -> User:
    logger.info(f"Creating new user: {user_in.email}")

    try:
        # Convert Pydantic model to DB model
        db_user = User(**user_in.model_dump(exclude_unset=True))

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return db_user

    except IntegrityError as e:
        db.rollback()
        # Parse the error to see if it's email or auth_id (Postgres specific)
        if "auth_id" in str(e.orig):
            raise UserAlreadyExistsException(f"Auth ID {user_in.auth_id}")
        if "email" in str(e.orig):
            raise UserAlreadyExistsException(f"Email {user_in.email}")

        # Fallback for other integrity errors
        logger.error(f"Integrity error creating user: {e}")
        raise UserAlreadyExistsException("User constraint violation")

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"DB Error creating user: {e}")
        raise DatabaseSystemException(str(e))


def get_user(db: Session, user_id: int) -> User:
    logger.debug(f"Getting user: {user_id}")
    try:
        stmt = select(User).where(User.id == user_id)
        user = db.scalar(stmt)

        if not user:
            raise UserNotFoundException(user_id)

        return user
    except SQLAlchemyError as e:
        logger.error(f"DB Error fetching user by auth_id: {e}")
        raise DatabaseSystemException(str(e))


def get_user_details(db: Session, user_id: int) -> User:
    logger.debug(f"Getting detailed user info for user_id: {user_id}")
    try:
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                # Load all Workouts for this User
                selectinload(User.workouts).options(

                    # Inside Workouts, load the 'WorkoutExercise' link
                    selectinload(Workout.exercises).options(

                        # Load the Definition (e.g. "Bench Press")
                        selectinload(WorkoutExercise.exercise_catalog),

                        # Load the Performance Data (Sets, Reps, Weight)
                        selectinload(WorkoutExercise.sets)
                    )
                )
            )
        )

        user = db.scalar(stmt)

        if not user:
            raise UserNotFoundException(user_id)

        return user

    except SQLAlchemyError as e:
        logger.error(f"DB Error fetching user details: {e}")
        raise DatabaseSystemException(str(e))


def update_user(db: Session, user_id: int, user_in: UserUpdate) -> User:
    logger.info(f"Updating user id={user_id}")

    try:
        user = db.scalar(select(User).where(User.id == user_id))

        if not user:
            logger.warning(f"User {user_id} not found for update")
            raise UserNotFoundException(user_id)

        update_data = user_in.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            # Prevent updating ID or Auth_ID or Role or Email here
            if key not in ["id", "auth_id", "role", "email"]:
                setattr(user, key, value)

        db.commit()
        db.refresh(user)

        logger.info(f"User {user_id} updated successfully")
        return user

    except IntegrityError as e:
        db.rollback()
        # Handle unique constraint violations
        if "email" in str(e.orig):
            raise UserAlreadyExistsException(f"Email in use")
        if "username" in str(e.orig):
            raise UserAlreadyExistsException(f"Username in use")

        logger.error(f"Integrity error updating user: {e}")
        raise UserAlreadyExistsException("Update conflict")

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"DB Error updating user: {e}")
        raise DatabaseSystemException(str(e))


def delete_user(db: Session, user_id: int) -> None:
    logger.info(f"Deleting user id={user_id}")

    try:
        user = db.scalar(select(User).where(User.id == user_id))

        if not user:
            logger.warning(f"User {user_id} not found for delete")
            raise UserNotFoundException(user_id)

        db.delete(user)
        db.commit()

        logger.info(f"User {user_id} deleted")
        return None

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"DB Error deleting user: {e}")
        raise DatabaseSystemException(str(e))
