import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.user_schema import UserResponse, UserResponseDetails, UserUpdate
from app.services import user_service
from app.utils.auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get the current authenticated user's profile.
    """
    logger.info(f"User {current_user.id} fetching their profile")
    return current_user


@router.get("/me/details", response_model=UserResponseDetails)
async def get_current_user_details(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed user info including all workouts with exercises and sets.
    """
    logger.info(f"User {current_user.id} fetching detailed profile")
    return user_service.get_user_details(db, current_user.id)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update the current user's profile (username, etc.).
    """
    logger.info(f"User {current_user.id} updating their profile")
    return user_service.update_user(db, current_user.id, user_in)
