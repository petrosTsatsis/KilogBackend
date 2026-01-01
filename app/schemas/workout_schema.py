from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel

from .exercise_schema import ExerciseResponse
from .set_schema import SetCreate, SetResponse


class WorkoutExerciseBase(BaseModel):
    exercise_id: int


class WorkoutExerciseCreate(WorkoutExerciseBase):
    sets: List[SetCreate] = []


class WorkoutExerciseResponse(WorkoutExerciseBase):
    id: int
    workout_id: int

    exercise_catalog: ExerciseResponse
    sets: List[SetResponse] = []

    class Config:
        from_attributes = True


class WorkoutBase(BaseModel):
    date: date
    notes: Optional[str] = None


class WorkoutCreate(WorkoutBase):
    exercises: List[WorkoutExerciseCreate] = []


class WorkoutResponse(WorkoutBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    exercises: List[WorkoutExerciseResponse] = []

    class Config:
        from_attributes = True
