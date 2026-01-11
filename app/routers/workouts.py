import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.workout_schema import WorkoutCreate, WorkoutUpdate, WorkoutResponse
from app.services import workout_service
from app.utils.auth import get_current_user

router = APIRouter(prefix="/workouts", tags=["workouts"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[WorkoutResponse])
async def list_workouts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List workouts for the current user, ordered by date (newest first).
    """
    logger.info(f"User {current_user.id} listing workouts, limit={limit}, offset={offset}")
    workouts = workout_service.list_user_workouts(db, current_user.id, limit, offset)
    return workouts


@router.get("/{workout_id}", response_model=WorkoutResponse)
async def get_workout(
    workout_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific workout with all exercises and sets.
    """
    logger.info(f"User {current_user.id} getting workout {workout_id}")
    workout = workout_service.get_workout_by_id(db, workout_id, current_user.id)
    return workout


@router.post("", response_model=WorkoutResponse, status_code=201)
async def create_workout(
    workout_in: WorkoutCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new workout with exercises and sets.
    """
    logger.info(f"User {current_user.id} creating workout on {workout_in.date}")
    workout = workout_service.create_workout(db, workout_in, current_user.id)
    # Reload to get all relationships
    return workout_service.get_workout_by_id(db, workout.id, current_user.id)


@router.put("/{workout_id}", response_model=WorkoutResponse)
async def update_workout(
    workout_id: int,
    workout_in: WorkoutUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing workout. Replaces all exercises and sets.
    """
    logger.info(f"User {current_user.id} updating workout {workout_id}")
    workout = workout_service.update_workout(db, workout_id, workout_in, current_user.id)
    return workout_service.get_workout_by_id(db, workout.id, current_user.id)


@router.delete("/{workout_id}", status_code=204)
async def delete_workout(
    workout_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a workout and all its exercises and sets.
    """
    logger.info(f"User {current_user.id} deleting workout {workout_id}")
    workout_service.delete_workout(db, workout_id, current_user.id)
    return None
