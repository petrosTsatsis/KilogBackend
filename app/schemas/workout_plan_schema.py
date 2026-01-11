from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PlannedExercise(BaseModel):
    """A planned exercise within a workout plan day."""
    exercise_id: int
    exercise_name: Optional[str] = None  # For display purposes
    sets: int = Field(ge=1)
    reps: str  # e.g., "8-10" or "12"


class WorkoutPlanDayBase(BaseModel):
    """Base schema for a workout plan day."""
    day_of_week: int = Field(ge=0, le=6)  # 0=Monday, 6=Sunday
    is_rest_day: bool = False
    workout_name: Optional[str] = None
    exercises: Optional[List[PlannedExercise]] = None


class WorkoutPlanDayCreate(WorkoutPlanDayBase):
    """Schema for creating a workout plan day."""
    pass


class WorkoutPlanDayResponse(WorkoutPlanDayBase):
    """Schema for responding with a workout plan day."""
    id: int

    model_config = ConfigDict(from_attributes=True)


class WorkoutPlanBase(BaseModel):
    """Base schema for a workout plan."""
    name: str = Field(max_length=255, default="My Workout Plan")


class WorkoutPlanCreate(WorkoutPlanBase):
    """Schema for creating a workout plan."""
    days: List[WorkoutPlanDayCreate] = []
    is_active: bool = False


class WorkoutPlanUpdate(BaseModel):
    """Schema for updating a workout plan."""
    name: Optional[str] = Field(max_length=255, default=None)
    days: Optional[List[WorkoutPlanDayCreate]] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class WorkoutPlanResponse(WorkoutPlanBase):
    """Schema for responding with a workout plan."""
    id: int
    user_id: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    days: List[WorkoutPlanDayResponse] = []

    model_config = ConfigDict(from_attributes=True)


class TodayPlanResponse(BaseModel):
    """Schema for today's planned workout."""
    has_plan: bool = False
    is_rest_day: bool = False
    workout_name: Optional[str] = None
    exercises: Optional[List[PlannedExercise]] = None
    plan_name: Optional[str] = None
