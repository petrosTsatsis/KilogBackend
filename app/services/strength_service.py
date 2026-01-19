"""
Strength service for 1RM calculations and strength standard comparisons.
"""
import logging
import re
from typing import Optional, Dict

logger = logging.getLogger(__name__)


# Strength standards as body weight multipliers
# Format: {normalized_exercise_name: {level: multiplier}}
# Multipliers represent what percentage of body weight constitutes each level
STRENGTH_STANDARDS: Dict[str, Dict[str, float]] = {
    "bench_press": {"beginner": 0.5, "intermediate": 1.0, "advanced": 1.5, "elite": 2.0},
    "flat_bench_press": {"beginner": 0.5, "intermediate": 1.0, "advanced": 1.5, "elite": 2.0},
    "barbell_bench_press": {"beginner": 0.5, "intermediate": 1.0, "advanced": 1.5, "elite": 2.0},
    "incline_bench_press": {"beginner": 0.4, "intermediate": 0.8, "advanced": 1.2, "elite": 1.6},
    "squat": {"beginner": 0.75, "intermediate": 1.25, "advanced": 1.75, "elite": 2.5},
    "back_squat": {"beginner": 0.75, "intermediate": 1.25, "advanced": 1.75, "elite": 2.5},
    "barbell_squat": {"beginner": 0.75, "intermediate": 1.25, "advanced": 1.75, "elite": 2.5},
    "front_squat": {"beginner": 0.6, "intermediate": 1.0, "advanced": 1.4, "elite": 2.0},
    "deadlift": {"beginner": 1.0, "intermediate": 1.5, "advanced": 2.0, "elite": 2.75},
    "conventional_deadlift": {"beginner": 1.0, "intermediate": 1.5, "advanced": 2.0, "elite": 2.75},
    "sumo_deadlift": {"beginner": 1.0, "intermediate": 1.5, "advanced": 2.0, "elite": 2.75},
    "romanian_deadlift": {"beginner": 0.6, "intermediate": 1.0, "advanced": 1.4, "elite": 1.8},
    "overhead_press": {"beginner": 0.35, "intermediate": 0.65, "advanced": 1.0, "elite": 1.35},
    "military_press": {"beginner": 0.35, "intermediate": 0.65, "advanced": 1.0, "elite": 1.35},
    "shoulder_press": {"beginner": 0.35, "intermediate": 0.65, "advanced": 1.0, "elite": 1.35},
    "barbell_row": {"beginner": 0.5, "intermediate": 0.85, "advanced": 1.2, "elite": 1.5},
    "bent_over_row": {"beginner": 0.5, "intermediate": 0.85, "advanced": 1.2, "elite": 1.5},
    "pendlay_row": {"beginner": 0.5, "intermediate": 0.85, "advanced": 1.2, "elite": 1.5},
    # Default for exercises not in the list
    "default": {"beginner": 0.5, "intermediate": 1.0, "advanced": 1.5, "elite": 2.0},
}


def calculate_1rm(weight: float, reps: int) -> float:
    """
    Calculate estimated 1 rep max using the Epley formula.

    Formula: 1RM = weight × (1 + reps/30)

    Args:
        weight: Weight lifted in kg
        reps: Number of reps performed

    Returns:
        Estimated 1RM in kg, rounded to 1 decimal place
    """
    if weight <= 0 or reps <= 0:
        return 0.0

    # For 1 rep, the weight IS the 1RM
    if reps == 1:
        return round(weight, 1)

    estimated_1rm = weight * (1 + reps / 30)
    return round(estimated_1rm, 1)


def normalize_exercise_name(name: str) -> str:
    """
    Normalize exercise name for lookup in strength standards.

    Converts to lowercase, replaces spaces/special chars with underscores,
    and removes common suffixes.

    Args:
        name: Original exercise name

    Returns:
        Normalized name for lookup
    """
    # Convert to lowercase
    normalized = name.lower()

    # Replace spaces and hyphens with underscores
    normalized = re.sub(r'[\s\-]+', '_', normalized)

    # Remove parenthetical notes like "(barbell)" or "(dumbbell)"
    normalized = re.sub(r'\([^)]*\)', '', normalized)

    # Remove trailing underscores
    normalized = normalized.strip('_')

    return normalized


def get_strength_standards_for_exercise(exercise_name: str) -> Dict[str, float]:
    """
    Get the strength standard multipliers for an exercise.

    Args:
        exercise_name: Name of the exercise

    Returns:
        Dict with beginner/intermediate/advanced/elite multipliers
    """
    normalized = normalize_exercise_name(exercise_name)

    # Try exact match first
    if normalized in STRENGTH_STANDARDS:
        return STRENGTH_STANDARDS[normalized]

    # Try partial match (exercise name contains a known exercise)
    for known_exercise, standards in STRENGTH_STANDARDS.items():
        if known_exercise != "default" and known_exercise in normalized:
            return standards

    # Return default standards
    return STRENGTH_STANDARDS["default"]


def get_strength_thresholds(body_weight: float, exercise_name: str) -> Dict[str, float]:
    """
    Calculate the actual weight thresholds for each strength level.

    Args:
        body_weight: User's body weight in kg
        exercise_name: Name of the exercise

    Returns:
        Dict with weight thresholds for each level (in kg)
    """
    if body_weight <= 0:
        return {}

    standards = get_strength_standards_for_exercise(exercise_name)

    return {
        "beginner": round(body_weight * standards["beginner"], 1),
        "intermediate": round(body_weight * standards["intermediate"], 1),
        "advanced": round(body_weight * standards["advanced"], 1),
        "elite": round(body_weight * standards["elite"], 1),
    }


def get_strength_level(
    estimated_1rm: float,
    body_weight: Optional[float],
    exercise_name: str
) -> str:
    """
    Determine strength level based on estimated 1RM and body weight.

    Args:
        estimated_1rm: Estimated 1 rep max in kg
        body_weight: User's body weight in kg (None if not set)
        exercise_name: Name of the exercise

    Returns:
        Strength level: "beginner", "intermediate", "advanced", "elite", or "unknown"
    """
    if body_weight is None or body_weight <= 0:
        return "unknown"

    if estimated_1rm <= 0:
        return "beginner"

    thresholds = get_strength_thresholds(body_weight, exercise_name)

    if estimated_1rm >= thresholds["elite"]:
        return "elite"
    elif estimated_1rm >= thresholds["advanced"]:
        return "advanced"
    elif estimated_1rm >= thresholds["intermediate"]:
        return "intermediate"
    else:
        return "beginner"


def get_percentage_to_next_level(
    estimated_1rm: float,
    body_weight: Optional[float],
    exercise_name: str
) -> Optional[float]:
    """
    Calculate progress percentage toward the next strength level.

    Args:
        estimated_1rm: Estimated 1 rep max in kg
        body_weight: User's body weight in kg
        exercise_name: Name of the exercise

    Returns:
        Percentage (0-100) toward next level, or None if at elite or unknown
    """
    if body_weight is None or body_weight <= 0 or estimated_1rm <= 0:
        return None

    current_level = get_strength_level(estimated_1rm, body_weight, exercise_name)

    if current_level in ["elite", "unknown"]:
        return None

    thresholds = get_strength_thresholds(body_weight, exercise_name)

    # Determine current and next threshold
    levels = ["beginner", "intermediate", "advanced", "elite"]
    current_idx = levels.index(current_level)
    next_level = levels[current_idx + 1]

    current_threshold = thresholds[current_level]
    next_threshold = thresholds[next_level]

    # Calculate progress within current level
    range_size = next_threshold - current_threshold
    progress = estimated_1rm - current_threshold

    percentage = (progress / range_size) * 100
    return round(min(max(percentage, 0), 100), 1)
