from typing import Optional

from pydantic import BaseModel


class ExerciseBase(BaseModel):
    name: str
    category: Optional[str] = None


class ExerciseCreate(ExerciseBase):
    pass


class ExerciseResponse(ExerciseBase):
    id: int
    user_id: Optional[int] = None

    class Config:
        from_attributes = True
