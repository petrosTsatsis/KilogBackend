import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.services import analytics_service, progression_service
from app.utils.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)


# --- Response Models ---

class PersonalBestResponse(BaseModel):
    exercise_id: int
    max_weight: Optional[float]


class ProgressDataPoint(BaseModel):
    date: str
    weight: float


class ConsistencyResponse(BaseModel):
    workouts_last_7_days: int


class ExerciseRecord(BaseModel):
    exercise_id: int
    exercise_name: str
    category: Optional[str]
    max_weight: float
    reps: int
    date_achieved: str


class SetHistoryItem(BaseModel):
    workout_id: int
    date: str
    workout_name: Optional[str]
    set_order: int
    weight: float
    reps: int
    rpe: Optional[float]


class SetDetail(BaseModel):
    order: int
    weight: float
    reps: int
    rpe: Optional[float]


class PreviousLiftResponse(BaseModel):
    workout_id: int
    date: str
    workout_name: Optional[str]
    sets: list[SetDetail]


class RecordHistoryItem(BaseModel):
    date: str
    weight: float
    is_current_pr: bool


class ExerciseSummary(BaseModel):
    exercise_id: int
    exercise_name: str
    category: Optional[str]
    sets_count: int
    top_weight: float


class WorkoutHistoryItem(BaseModel):
    id: int
    name: Optional[str]
    date: str
    notes: Optional[str]
    total_volume: float
    total_sets: int
    exercises_count: int
    exercises: list[ExerciseSummary]


class WorkoutHistoryResponse(BaseModel):
    total: int
    workouts: list[WorkoutHistoryItem]


class VolumeDataPoint(BaseModel):
    date: str
    volume: float


class StatsSummaryResponse(BaseModel):
    total_workouts: int
    total_volume: float
    total_sets: int
    unique_exercises: int
    current_streak: int
    this_month_workouts: int


class StrengthThresholds(BaseModel):
    beginner: float
    intermediate: float
    advanced: float
    elite: float


class EnhancedExerciseRecord(BaseModel):
    exercise_id: int
    exercise_name: str
    category: Optional[str]
    max_weight: float
    reps: int
    date_achieved: str
    estimated_1rm: float
    strength_level: str  # beginner, intermediate, advanced, elite, unknown
    strength_thresholds: Optional[StrengthThresholds]
    percentage_to_next_level: Optional[float]


class ProgressionSuggestionResponse(BaseModel):
    suggested_weight: float
    suggested_reps: int
    strategy: str  # strength, hypertrophy
    explanation: str
    previous_weight: float
    previous_reps: int


# --- Endpoints ---

@router.get("/exercises/{exercise_id}/pb", response_model=PersonalBestResponse)
async def get_personal_best(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the personal best (max weight) for a specific exercise.
    """
    logger.info(f"User {current_user.id} getting PB for exercise {exercise_id}")
    max_weight = analytics_service.get_personal_best(db, current_user.id, exercise_id)
    return PersonalBestResponse(exercise_id=exercise_id, max_weight=max_weight)


@router.get("/exercises/{exercise_id}/progress", response_model=list[ProgressDataPoint])
async def get_exercise_progress(
    exercise_id: int,
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get progress data for an exercise (date vs max weight per session).
    Useful for charting progress over time.
    """
    logger.info(f"User {current_user.id} getting progress for exercise {exercise_id}")
    data = analytics_service.get_exercise_progress(db, current_user.id, exercise_id, limit)
    return [
        ProgressDataPoint(date=str(point["date"]), weight=point["weight"])
        for point in data
    ]


@router.get("/exercises/{exercise_id}/history", response_model=list[SetHistoryItem])
async def get_exercise_history(
    exercise_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get full set history for an exercise with optional date filtering.
    """
    logger.info(f"User {current_user.id} getting history for exercise {exercise_id}")
    data = analytics_service.get_exercise_history(
        db, current_user.id, exercise_id, start_date, end_date, limit
    )
    return [SetHistoryItem(**item) for item in data]


@router.get("/exercises/{exercise_id}/previous", response_model=Optional[PreviousLiftResponse])
async def get_previous_lift(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the most recent performance for an exercise.
    """
    logger.info(f"User {current_user.id} getting previous lift for exercise {exercise_id}")
    data = analytics_service.get_previous_lift(db, current_user.id, exercise_id)
    if not data:
        return None
    return PreviousLiftResponse(**data)


@router.get("/exercises/{exercise_id}/records", response_model=list[RecordHistoryItem])
async def get_record_history(
    exercise_id: int,
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the history of personal records for an exercise.
    Shows when each PR was achieved over time.
    """
    logger.info(f"User {current_user.id} getting record history for exercise {exercise_id}")
    data = analytics_service.get_record_history(db, current_user.id, exercise_id, limit)
    return [RecordHistoryItem(**item) for item in data]


@router.get("/consistency", response_model=ConsistencyResponse)
async def get_weekly_consistency(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the number of workouts completed in the last 7 days.
    """
    logger.info(f"User {current_user.id} checking weekly consistency")
    count = analytics_service.get_weekly_consistency(db, current_user.id)
    return ConsistencyResponse(workouts_last_7_days=count)


@router.get("/records", response_model=list[ExerciseRecord])
async def get_all_exercise_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get personal bests for all exercises the user has performed.
    """
    logger.info(f"User {current_user.id} getting all exercise records")
    data = analytics_service.get_all_exercise_records(db, current_user.id)
    return [ExerciseRecord(**item) for item in data]


@router.get("/history", response_model=WorkoutHistoryResponse)
async def get_workout_history(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    exercise_id: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get workout history with optional filters (date range, exercise, category).
    """
    logger.info(f"User {current_user.id} getting workout history")
    data = analytics_service.get_workout_history(
        db, current_user.id, start_date, end_date, exercise_id, category, limit, offset
    )
    return WorkoutHistoryResponse(**data)


@router.get("/volume", response_model=list[VolumeDataPoint])
async def get_volume_over_time(
    days: int = Query(30, ge=7, le=365),
    exercise_id: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get daily volume data for charting over a time period.
    """
    logger.info(f"User {current_user.id} getting volume over last {days} days")
    data = analytics_service.get_volume_over_time(
        db, current_user.id, days, exercise_id, category
    )
    return [VolumeDataPoint(**item) for item in data]


@router.get("/summary", response_model=StatsSummaryResponse)
async def get_stats_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get overall stats summary for the user.
    """
    logger.info(f"User {current_user.id} getting stats summary")
    data = analytics_service.get_stats_summary(db, current_user.id)
    return StatsSummaryResponse(**data)


@router.get("/records/enhanced", response_model=list[EnhancedExerciseRecord])
async def get_enhanced_exercise_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get personal bests with 1RM estimates and strength levels.
    Includes estimated 1RM, strength level classification, and progress to next level.
    """
    logger.info(f"User {current_user.id} getting enhanced exercise records")
    data = analytics_service.get_all_exercise_records_with_1rm(db, current_user.id)
    return [EnhancedExerciseRecord(**item) for item in data]


@router.get("/exercises/{exercise_id}/suggestion", response_model=Optional[ProgressionSuggestionResponse])
async def get_progression_suggestion(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get smart progression suggestion for an exercise.
    Analyzes previous performance and user's fitness goal to suggest
    appropriate weight and rep targets for the next workout.
    """
    logger.info(f"User {current_user.id} getting progression suggestion for exercise {exercise_id}")
    data = progression_service.get_progression_suggestion(db, current_user.id, exercise_id)
    if not data:
        return None
    return ProgressionSuggestionResponse(**data)
