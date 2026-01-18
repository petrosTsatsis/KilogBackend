from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class FitnessGoal(str, Enum):
    LOSE_WEIGHT = "LOSE_WEIGHT"
    BUILD_MUSCLE = "BUILD_MUSCLE"
    GET_STRONGER = "GET_STRONGER"
    IMPROVE_ENDURANCE = "IMPROVE_ENDURANCE"
    GENERAL_FITNESS = "GENERAL_FITNESS"
    TONE_UP = "TONE_UP"
    BULK = "BULK"
    CUT = "CUT"
    ATHLETIC_PERFORMANCE = "ATHLETIC_PERFORMANCE"
    FLEXIBILITY = "FLEXIBILITY"


class ExperienceLevel(str, Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class EquipmentAccess(str, Enum):
    GYM = "GYM"
    HOME = "HOME"
    BODYWEIGHT = "BODYWEIGHT"


class UserProfileCreate(BaseModel):
    primary_goal: FitnessGoal
    secondary_goals: Optional[List[FitnessGoal]] = None
    training_days_per_week: int = Field(ge=2, le=6)
    experience_level: ExperienceLevel
    equipment_access: EquipmentAccess
    age: Optional[int] = Field(None, ge=13, le=120)
    weight_kg: Optional[float] = Field(None, gt=0)
    height_cm: Optional[float] = Field(None, gt=0)


class UserProfileUpdate(BaseModel):
    primary_goal: Optional[FitnessGoal] = None
    secondary_goals: Optional[List[FitnessGoal]] = None
    training_days_per_week: Optional[int] = Field(None, ge=2, le=6)
    experience_level: Optional[ExperienceLevel] = None
    equipment_access: Optional[EquipmentAccess] = None
    age: Optional[int] = Field(None, ge=13, le=120)
    weight_kg: Optional[float] = Field(None, gt=0)
    height_cm: Optional[float] = Field(None, gt=0)


class UserProfileResponse(BaseModel):
    id: int
    user_id: int
    primary_goal: Optional[FitnessGoal] = None
    secondary_goals: Optional[List[str]] = None
    training_days_per_week: Optional[int] = None
    experience_level: Optional[ExperienceLevel] = None
    equipment_access: Optional[EquipmentAccess] = None
    age: Optional[int] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    onboarding_completed: bool
    onboarding_completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OnboardingStatusResponse(BaseModel):
    needs_onboarding: bool
    onboarding_completed: bool
    onboarding_completed_at: Optional[datetime] = None


class WorkoutPlanRecommendation(BaseModel):
    template_id: str
    name: str
    description: str
    match_score: int
    match_reasons: List[str]
    days_per_week: int


class OnboardingRecommendationsResponse(BaseModel):
    recommended_plans: List[WorkoutPlanRecommendation]
    personalized_tips: List[str]
    goal_specific_advice: str
