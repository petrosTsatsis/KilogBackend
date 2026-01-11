from sqlalchemy import Column, Integer, ForeignKey, Date, func, Text, String
from sqlalchemy.orm import relationship

from ..database import Base


class Workout(Base):
    """
    A single gym session.
    """
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(255), nullable=True)
    date = Column(Date, default=func.now())
    notes = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="workouts")
    # 'cascade="all, delete-orphan"' means if you delete the workout,
    # it automatically deletes all exercises associated with it.
    exercises = relationship("WorkoutExercise", back_populates="workout", cascade="all, delete-orphan")
