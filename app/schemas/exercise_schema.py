from typing import Optional

from pydantic import BaseModel, ConfigDict


class ExerciseBase(BaseModel):
    name: str
    category: Optional[str] = None


class ExerciseCreate(ExerciseBase):
    pass


class ExerciseUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None


class ExerciseResponse(ExerciseBase):
    id: int
    user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
