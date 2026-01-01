from typing import Optional

from pydantic import BaseModel


class SetBase(BaseModel):
    weight: float
    reps: int
    rpe: Optional[float] = None
    order: int = 1


class SetCreate(SetBase):
    pass


class SetResponse(SetBase):
    id: int
    workout_exercise_id: int

    class Config:
        from_attributes = True
