from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from ..database import Base


class Exercise(Base):
    """
    The Catalog of Exercises.
    e.g. "Bench Press", "Squat".
    If user_id is NULL, it is a global system exercise everyone sees.
    """
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String, nullable=True)  # e.g. "Push", "Pull", "Legs"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="exercises")
    workout_instances = relationship("WorkoutExercise", back_populates="exercise_catalog")
