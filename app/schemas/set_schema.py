from typing import Optional

from pydantic import BaseModel, ConfigDict


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

    model_config = ConfigDict(from_attributes=True)
