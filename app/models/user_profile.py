import enum

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class FitnessGoal(str, enum.Enum):
    LOSE_WEIGHT = "LOSE_WEIGHT"
    BUILD_MUSCLE = "BUILD_MUSCLE"
    GET_STRONGER = "GET_STRONGER"
    IMPROVE_ENDURANCE = "IMPROVE_ENDURANCE"
    GENERAL_FITNESS = "GENERAL_FITNESS"
    TONE_UP = "TONE_UP"
    BULK = "BULK"
    CUT = "CUT"
    ATHLETIC_PERFORMANCE = "ATHLETIC_PERFORMANCE"
    FLEXIBILITY = "FLEXIBILITY"


class ExperienceLevel(str, enum.Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class EquipmentAccess(str, enum.Enum):
    GYM = "GYM"
    HOME = "HOME"
    BODYWEIGHT = "BODYWEIGHT"


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Goals
    primary_goal = Column(SQLAlchemyEnum(FitnessGoal), nullable=True)
    secondary_goals = Column(ARRAY(String), nullable=True)

    # Training preferences
    training_days_per_week = Column(Integer, nullable=True)

    # Experience & Equipment
    experience_level = Column(SQLAlchemyEnum(ExperienceLevel), nullable=True)
    equipment_access = Column(SQLAlchemyEnum(EquipmentAccess), nullable=True)

    # Physical profile
    age = Column(Integer, nullable=True)
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)

    # Onboarding tracking
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    onboarding_completed_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    user = relationship("User", back_populates="profile")
