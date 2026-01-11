from sqlalchemy import Column, Integer, ForeignKey, Boolean, String, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class WorkoutPlan(Base):
    """
    A weekly workout plan for scheduling workouts.
    Each user can have multiple plans but only one active at a time.
    """
    __tablename__ = "workout_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False, default="My Workout Plan")
    is_active = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="workout_plans")
    days = relationship("WorkoutPlanDay", back_populates="plan", cascade="all, delete-orphan")


class WorkoutPlanDay(Base):
    """
    A single day in a weekly workout plan.
    day_of_week: 0=Monday, 1=Tuesday, ..., 6=Sunday
    """
    __tablename__ = "workout_plan_days"

    id = Column(Integer, primary_key=True, index=True)
    workout_plan_id = Column(Integer, ForeignKey("workout_plans.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0-6 (Mon-Sun)
    is_rest_day = Column(Boolean, default=False, nullable=False)
    workout_name = Column(String(255), nullable=True)
    # Store planned exercises as JSON: [{"exercise_id": 1, "sets": 4, "reps": "8-10"}, ...]
    exercises = Column(JSON, nullable=True)

    # Relationships
    plan = relationship("WorkoutPlan", back_populates="days")
