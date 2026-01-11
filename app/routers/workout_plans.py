import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.workout_plan_schema import (
    WorkoutPlanCreate, WorkoutPlanUpdate, WorkoutPlanResponse, TodayPlanResponse
)
from app.services import workout_plan_service
from app.utils.auth import get_current_user

router = APIRouter(prefix="/workout-plans", tags=["workout-plans"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[WorkoutPlanResponse])
async def list_workout_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all workout plans for the current user.
    """
    logger.info(f"User {current_user.id} listing workout plans")
    plans = workout_plan_service.list_user_workout_plans(db, current_user.id)
    return plans


@router.get("/active", response_model=WorkoutPlanResponse | None)
async def get_active_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the currently active workout plan for the user.
    """
    logger.info(f"User {current_user.id} getting active plan")
    plan = workout_plan_service.get_active_plan(db, current_user.id)
    return plan


@router.get("/today", response_model=TodayPlanResponse)
async def get_today_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get today's planned workout based on the active plan.
    """
    logger.info(f"User {current_user.id} getting today's plan")
    return workout_plan_service.get_today_plan(db, current_user.id)


@router.get("/{plan_id}", response_model=WorkoutPlanResponse)
async def get_workout_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific workout plan.
    """
    logger.info(f"User {current_user.id} getting workout plan {plan_id}")
    plan = workout_plan_service.get_workout_plan_by_id(db, plan_id, current_user.id)
    return plan


@router.post("", response_model=WorkoutPlanResponse, status_code=201)
async def create_workout_plan(
    plan_in: WorkoutPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new workout plan.
    """
    logger.info(f"User {current_user.id} creating workout plan '{plan_in.name}'")
    plan = workout_plan_service.create_workout_plan(db, plan_in, current_user.id)
    return plan


@router.put("/{plan_id}", response_model=WorkoutPlanResponse)
async def update_workout_plan(
    plan_id: int,
    plan_in: WorkoutPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing workout plan.
    """
    logger.info(f"User {current_user.id} updating workout plan {plan_id}")
    plan = workout_plan_service.update_workout_plan(db, plan_id, plan_in, current_user.id)
    return plan


@router.post("/{plan_id}/activate", response_model=WorkoutPlanResponse)
async def activate_workout_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Set a workout plan as the active plan.
    """
    logger.info(f"User {current_user.id} activating workout plan {plan_id}")
    plan = workout_plan_service.set_plan_active(db, plan_id, current_user.id)
    return plan


@router.delete("/{plan_id}", status_code=204)
async def delete_workout_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a workout plan.
    """
    logger.info(f"User {current_user.id} deleting workout plan {plan_id}")
    workout_plan_service.delete_workout_plan(db, plan_id, current_user.id)
    return None
