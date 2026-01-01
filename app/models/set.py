from sqlalchemy import Column, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship

from ..database import Base


class Set(Base):
    """
    The actual performance data.
    """
    __tablename__ = "sets"

    id = Column(Integer, primary_key=True, index=True)
    workout_exercise_id = Column(Integer, ForeignKey("workout_exercises.id"))

    order = Column(Integer, default=1)  # 1st set, 2nd set...
    weight = Column(Float)  # Float for 2.5kg increments
    reps = Column(Integer)
    rpe = Column(Float, nullable=True)  # Rate of Perceived Exertion

    # Relationships
    workout_exercise = relationship("WorkoutExercise", back_populates="sets")
