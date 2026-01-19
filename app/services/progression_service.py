"""
Progressive overload suggestion service.
Generates smart weight/rep recommendations based on user goals and history.
"""
import logging
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models.user_profile import FitnessGoal, UserProfile
from app.services import analytics_service

logger = logging.getLogger(__name__)

# Weight increment for progression (in kg)
WEIGHT_INCREMENT = 2.5

# Rep ranges for different strategies
HYPERTROPHY_MIN_REPS = 8
HYPERTROPHY_MAX_REPS = 12
STRENGTH_MIN_REPS = 3
STRENGTH_MAX_REPS = 6


def get_user_goal(db: Session, user_id: int) -> Optional[FitnessGoal]:
    """
    Get the user's primary fitness goal from their profile.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        FitnessGoal enum value or None if not set
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if profile and profile.primary_goal:
        return profile.primary_goal
    return None


def _calculate_averages(sets: list[Dict[str, Any]]) -> tuple[float, float]:
    """
    Calculate average weight and reps from a list of sets.

    Args:
        sets: List of set dictionaries with 'weight' and 'reps' keys

    Returns:
        Tuple of (average_weight, average_reps)
    """
    if not sets:
        return 0.0, 0.0

    total_weight = sum(s.get("weight", 0) or 0 for s in sets)
    total_reps = sum(s.get("reps", 0) or 0 for s in sets)

    avg_weight = total_weight / len(sets)
    avg_reps = total_reps / len(sets)

    return avg_weight, avg_reps


def _strength_progression(previous_lift: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate progression suggestion for strength-focused goals.

    Strategy: Prioritize weight increase while maintaining rep range (3-6).
    - If below max rep range: suggest same weight, +1 rep
    - If at or above max rep range: suggest +2.5kg, reset to min reps

    Args:
        previous_lift: Previous lift data with 'sets' list

    Returns:
        Progression suggestion dictionary
    """
    sets = previous_lift.get("sets", [])
    avg_weight, avg_reps = _calculate_averages(sets)

    # Round to nearest integer for reps
    current_reps = round(avg_reps)

    if current_reps < STRENGTH_MAX_REPS:
        # Increase reps at same weight
        suggested_weight = round(avg_weight, 1)
        suggested_reps = min(current_reps + 1, STRENGTH_MAX_REPS)
        explanation = f"Build strength: aim for {suggested_reps} reps at {suggested_weight}kg"
    else:
        # Increase weight, reset reps
        suggested_weight = round(avg_weight + WEIGHT_INCREMENT, 1)
        suggested_reps = STRENGTH_MIN_REPS
        explanation = f"Time to progress! Try {suggested_weight}kg for {suggested_reps} reps"

    return {
        "suggested_weight": suggested_weight,
        "suggested_reps": suggested_reps,
        "strategy": "strength",
        "explanation": explanation,
        "previous_weight": round(avg_weight, 1),
        "previous_reps": current_reps,
    }


def _hypertrophy_progression(previous_lift: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate progression suggestion for hypertrophy-focused goals.

    Strategy: Prioritize rep increase within 8-12 range, then weight.
    - If below max rep range: suggest same weight, +1 rep
    - If at or above max rep range: suggest +2.5kg, reset to min reps

    Args:
        previous_lift: Previous lift data with 'sets' list

    Returns:
        Progression suggestion dictionary
    """
    sets = previous_lift.get("sets", [])
    avg_weight, avg_reps = _calculate_averages(sets)

    # Round to nearest integer for reps
    current_reps = round(avg_reps)

    if current_reps < HYPERTROPHY_MAX_REPS:
        # Increase reps at same weight
        suggested_weight = round(avg_weight, 1)
        suggested_reps = min(current_reps + 1, HYPERTROPHY_MAX_REPS + 3)  # Allow slight overshoot
        explanation = f"Push for {suggested_reps} reps at {suggested_weight}kg"
    else:
        # Increase weight, reset reps
        suggested_weight = round(avg_weight + WEIGHT_INCREMENT, 1)
        suggested_reps = HYPERTROPHY_MIN_REPS
        explanation = f"Great progress! Increase to {suggested_weight}kg for {suggested_reps} reps"

    return {
        "suggested_weight": suggested_weight,
        "suggested_reps": suggested_reps,
        "strategy": "hypertrophy",
        "explanation": explanation,
        "previous_weight": round(avg_weight, 1),
        "previous_reps": current_reps,
    }


def _bodyweight_progression(previous_lift: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate progression suggestion for bodyweight exercises (0 or minimal weight).

    Strategy: Focus purely on rep increase.

    Args:
        previous_lift: Previous lift data with 'sets' list

    Returns:
        Progression suggestion dictionary
    """
    sets = previous_lift.get("sets", [])
    _, avg_reps = _calculate_averages(sets)

    current_reps = round(avg_reps)
    suggested_reps = current_reps + 1

    return {
        "suggested_weight": 0.0,
        "suggested_reps": suggested_reps,
        "strategy": "hypertrophy",
        "explanation": f"Aim for {suggested_reps} reps this time",
        "previous_weight": 0.0,
        "previous_reps": current_reps,
    }


def get_progression_suggestion(
    db: Session,
    user_id: int,
    exercise_id: int
) -> Optional[Dict[str, Any]]:
    """
    Generate a smart progression suggestion for an exercise.

    Analyzes the user's previous performance and fitness goal to suggest
    appropriate weight and rep targets for the next workout.

    Args:
        db: Database session
        user_id: User ID
        exercise_id: Exercise ID to get suggestion for

    Returns:
        Progression suggestion dict or None if no previous data
    """
    # Get previous lift data
    previous_lift = analytics_service.get_previous_lift(db, user_id, exercise_id)

    if not previous_lift or not previous_lift.get("sets"):
        logger.debug(f"No previous lift data for user {user_id}, exercise {exercise_id}")
        return None

    # Check if this is a bodyweight exercise (avg weight near 0)
    avg_weight, _ = _calculate_averages(previous_lift.get("sets", []))
    if avg_weight < 1:  # Less than 1kg = bodyweight exercise
        return _bodyweight_progression(previous_lift)

    # Get user's goal to determine progression strategy
    goal = get_user_goal(db, user_id)

    # Strength-focused goals
    strength_goals = [
        FitnessGoal.GET_STRONGER,
        FitnessGoal.BULK,
        FitnessGoal.ATHLETIC_PERFORMANCE,
    ]

    if goal in strength_goals:
        return _strength_progression(previous_lift)
    else:
        # Default to hypertrophy for all other goals
        # (BUILD_MUSCLE, LOSE_WEIGHT, TONE_UP, GENERAL_FITNESS, CUT, etc.)
        return _hypertrophy_progression(previous_lift)
