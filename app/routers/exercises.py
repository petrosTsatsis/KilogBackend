import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.exercise_schema import ExerciseCreate, ExerciseUpdate, ExerciseResponse
from app.services import exercise_service
from app.utils.auth import get_current_user

router = APIRouter(prefix="/exercises", tags=["exercises"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[ExerciseResponse])
async def list_exercises(
    search: Optional[str] = Query(None, description="Search exercises by name"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all exercises available to the current user.
    Includes both system exercises and user's custom exercises.
    """
    logger.info(f"User {current_user.id} listing exercises, search={search}")
    exercises = exercise_service.list_exercises(db, current_user.id, search, limit)
    return exercises


@router.get("/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific exercise by ID.
    """
    logger.info(f"User {current_user.id} getting exercise {exercise_id}")
    exercise = exercise_service.get_exercise_by_id(db, exercise_id, current_user.id)
    return exercise


@router.post("", response_model=ExerciseResponse, status_code=201)
async def create_exercise(
    exercise_in: ExerciseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new custom exercise for the current user.
    """
    logger.info(f"User {current_user.id} creating exercise: {exercise_in.name}")
    exercise = exercise_service.create_custom_exercise(db, exercise_in, current_user.id)
    return exercise


@router.put("/{exercise_id}", response_model=ExerciseResponse)
async def update_exercise(
    exercise_id: int,
    exercise_in: ExerciseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a custom exercise. Only the owner can update their exercises.
    System exercises cannot be updated.
    """
    logger.info(f"User {current_user.id} updating exercise {exercise_id}")
    exercise = exercise_service.update_exercise(db, exercise_id, exercise_in, current_user.id)
    return exercise


@router.delete("/{exercise_id}", status_code=204)
async def delete_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a custom exercise. Only the owner can delete their exercises.
    System exercises cannot be deleted.
    """
    logger.info(f"User {current_user.id} deleting exercise {exercise_id}")
    exercise_service.delete_exercise(db, exercise_id, current_user.id)
    return None
