from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from ..database import Base


class WorkoutExercise(Base):
    """
    The link between a Workout (Session) and an Exercise (Catalog).
    This represents "I did Bench Press ON THIS DATE".
    """
    __tablename__ = "workout_exercises"

    id = Column(Integer, primary_key=True, index=True)
    workout_id = Column(Integer, ForeignKey("workouts.id"))
    exercise_id = Column(Integer, ForeignKey("exercises.id"))

    # Relationships
    workout = relationship("Workout", back_populates="exercises")
    exercise_catalog = relationship("Exercise", back_populates="workout_instances")
    sets = relationship("Set", back_populates="workout_exercise", cascade="all, delete-orphan")
