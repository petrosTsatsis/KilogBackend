import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.user_profile_schema import (
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
    OnboardingStatusResponse,
    OnboardingRecommendationsResponse,
)
from app.services import user_profile_service
from app.utils.auth import get_current_user

router = APIRouter(prefix="/onboarding", tags=["onboarding"])
logger = logging.getLogger(__name__)


@router.get("/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if the current user needs to complete onboarding."""
    profile = user_profile_service.get_profile(db, current_user.id)
    return OnboardingStatusResponse(
        needs_onboarding=profile is None or not profile.onboarding_completed,
        onboarding_completed=profile.onboarding_completed if profile else False,
        onboarding_completed_at=profile.onboarding_completed_at if profile else None,
    )


@router.post("/complete", response_model=UserProfileResponse)
async def complete_onboarding(
    data: UserProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit onboarding data and complete the onboarding flow."""
    logger.info(f"User {current_user.id} completing onboarding")
    profile = user_profile_service.create_or_update_profile(db, current_user.id, data)
    return profile


@router.get("/recommendations", response_model=OnboardingRecommendationsResponse)
async def get_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get personalized workout plan recommendations based on profile."""
    profile = user_profile_service.get_or_create_profile(db, current_user.id)

    recommendations = user_profile_service.get_plan_recommendations(profile)
    tips = user_profile_service.get_personalized_tips(profile)
    advice = user_profile_service.get_goal_specific_advice(profile)

    return OnboardingRecommendationsResponse(
        recommended_plans=recommendations,
        personalized_tips=tips,
        goal_specific_advice=advice,
    )


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current user's profile/preferences."""
    profile = user_profile_service.get_or_create_profile(db, current_user.id)
    return profile


@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user preferences (can be done after onboarding)."""
    logger.info(f"User {current_user.id} updating profile")
    profile = user_profile_service.update_profile(db, current_user.id, data)
    return profile
