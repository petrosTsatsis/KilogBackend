from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.models.user import Role
from .workout_schema import WorkoutResponse


class UserBase(BaseModel):
    email: str
    username: str


class UserCreate(UserBase):
    auth_id: str


class UserUpdate(BaseModel):
    # name, url, description etc.
    last_login_at: Optional[datetime] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime
    role: Role


class UserResponseDetails(UserResponse):
    workouts: List[WorkoutResponse] = []

    model_config = ConfigDict(from_attributes=True)
