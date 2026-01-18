import logging
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user_profile import (
    UserProfile,
    FitnessGoal as ModelFitnessGoal,
    ExperienceLevel as ModelExperienceLevel,
    EquipmentAccess as ModelEquipmentAccess,
)
from app.schemas.user_profile_schema import (
    UserProfileCreate,
    UserProfileUpdate,
    WorkoutPlanRecommendation,
    FitnessGoal,
    ExperienceLevel,
    EquipmentAccess,
)
from app.core.exceptions import ResourceNotFoundException

logger = logging.getLogger(__name__)


def get_or_create_profile(db: Session, user_id: int) -> UserProfile:
    """Get existing profile or create empty one."""
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def get_profile(db: Session, user_id: int) -> Optional[UserProfile]:
    """Get user profile if exists."""
    return db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))


def create_or_update_profile(db: Session, user_id: int, data: UserProfileCreate) -> UserProfile:
    """Create or update user profile from onboarding data."""
    profile = get_or_create_profile(db, user_id)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "secondary_goals" and value:
            value = [g.value if hasattr(g, "value") else g for g in value]
        elif key == "primary_goal" and value:
            value = ModelFitnessGoal(value.value if hasattr(value, "value") else value)
        elif key == "experience_level" and value:
            value = ModelExperienceLevel(value.value if hasattr(value, "value") else value)
        elif key == "equipment_access" and value:
            value = ModelEquipmentAccess(value.value if hasattr(value, "value") else value)
        setattr(profile, key, value)

    profile.onboarding_completed = True
    profile.onboarding_completed_at = datetime.utcnow()

    db.commit()
    db.refresh(profile)
    return profile


def update_profile(db: Session, user_id: int, data: UserProfileUpdate) -> UserProfile:
    """Update existing profile preferences."""
    profile = get_profile(db, user_id)
    if not profile:
        raise ResourceNotFoundException("UserProfile", user_id)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "secondary_goals" and value:
            value = [g.value if hasattr(g, "value") else g for g in value]
        elif key == "primary_goal" and value:
            value = ModelFitnessGoal(value.value if hasattr(value, "value") else value)
        elif key == "experience_level" and value:
            value = ModelExperienceLevel(value.value if hasattr(value, "value") else value)
        elif key == "equipment_access" and value:
            value = ModelEquipmentAccess(value.value if hasattr(value, "value") else value)
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    return profile


def needs_onboarding(db: Session, user_id: int) -> bool:
    """Check if user needs to complete onboarding."""
    profile = get_profile(db, user_id)
    return profile is None or not profile.onboarding_completed


def get_plan_recommendations(profile: UserProfile) -> List[WorkoutPlanRecommendation]:
    """Generate workout plan recommendations based on user profile."""
    recommendations = []

    goal = profile.primary_goal
    days = profile.training_days_per_week or 3
    experience = profile.experience_level
    equipment = profile.equipment_access

    # Define plan templates with scoring criteria
    plan_configs = [
        {
            "id": "full-body-3day",
            "name": "Full Body (3-Day)",
            "description": "Efficient full body workouts perfect for beginners or busy schedules. Train all major muscle groups each session.",
            "days": 3,
            "best_for_goals": [
                ModelFitnessGoal.GENERAL_FITNESS,
                ModelFitnessGoal.LOSE_WEIGHT,
                ModelFitnessGoal.TONE_UP,
                ModelFitnessGoal.IMPROVE_ENDURANCE,
            ],
            "best_for_experience": [ModelExperienceLevel.BEGINNER, ModelExperienceLevel.INTERMEDIATE],
            "requires_gym": True,
        },
        {
            "id": "strength-3day",
            "name": "Starting Strength (3-Day)",
            "description": "Linear progression program focused on compound lifts. Build a foundation of strength with squats, bench, and deadlifts.",
            "days": 3,
            "best_for_goals": [ModelFitnessGoal.GET_STRONGER, ModelFitnessGoal.BUILD_MUSCLE],
            "best_for_experience": [ModelExperienceLevel.BEGINNER],
            "requires_gym": True,
        },
        {
            "id": "upper-lower-4day",
            "name": "Upper Lower (4-Day)",
            "description": "Balanced split for strength and muscle with adequate recovery. Train upper and lower body twice per week.",
            "days": 4,
            "best_for_goals": [
                ModelFitnessGoal.BUILD_MUSCLE,
                ModelFitnessGoal.GET_STRONGER,
                ModelFitnessGoal.TONE_UP,
                ModelFitnessGoal.GENERAL_FITNESS,
            ],
            "best_for_experience": [ModelExperienceLevel.INTERMEDIATE, ModelExperienceLevel.ADVANCED],
            "requires_gym": True,
        },
        {
            "id": "push-pull-4day",
            "name": "Push Pull (4-Day)",
            "description": "Simple and effective split alternating push and pull movements. Great for building muscle efficiently.",
            "days": 4,
            "best_for_goals": [ModelFitnessGoal.BUILD_MUSCLE, ModelFitnessGoal.GENERAL_FITNESS],
            "best_for_experience": [ModelExperienceLevel.INTERMEDIATE],
            "requires_gym": True,
        },
        {
            "id": "bro-split-5day",
            "name": "Bro Split (5-Day)",
            "description": "Classic bodybuilding split targeting one muscle group per day. High volume for maximum muscle growth.",
            "days": 5,
            "best_for_goals": [ModelFitnessGoal.BUILD_MUSCLE, ModelFitnessGoal.BULK],
            "best_for_experience": [ModelExperienceLevel.INTERMEDIATE, ModelExperienceLevel.ADVANCED],
            "requires_gym": True,
        },
        {
            "id": "ppl-6day",
            "name": "Push Pull Legs (6-Day)",
            "description": "Classic PPL split training each muscle group twice per week. Ideal for serious lifters seeking maximum gains.",
            "days": 6,
            "best_for_goals": [
                ModelFitnessGoal.BUILD_MUSCLE,
                ModelFitnessGoal.BULK,
                ModelFitnessGoal.CUT,
                ModelFitnessGoal.ATHLETIC_PERFORMANCE,
            ],
            "best_for_experience": [ModelExperienceLevel.INTERMEDIATE, ModelExperienceLevel.ADVANCED],
            "requires_gym": True,
        },
    ]

    for plan in plan_configs:
        score = 0
        reasons = []

        # Days match (40 points max)
        if plan["days"] == days:
            score += 40
            reasons.append(f"Matches your {days} days/week schedule perfectly")
        elif abs(plan["days"] - days) == 1:
            score += 20
            reasons.append(f"Close to your preferred {days} days/week")

        # Goal match (35 points max)
        if goal and goal in plan["best_for_goals"]:
            score += 35
            goal_display = goal.value.replace("_", " ").title()
            reasons.append(f"Excellent for {goal_display}")

        # Experience match (15 points max)
        if experience and experience in plan["best_for_experience"]:
            score += 15
            reasons.append(f"Designed for {experience.value.lower()} level")
        elif experience == ModelExperienceLevel.ADVANCED and ModelExperienceLevel.BEGINNER in plan["best_for_experience"]:
            score -= 5

        # Equipment check (10 points max)
        if plan["requires_gym"] and equipment == ModelEquipmentAccess.GYM:
            score += 10
            reasons.append("Optimized for full gym equipment")
        elif not plan["requires_gym"]:
            score += 10
        elif plan["requires_gym"] and equipment == ModelEquipmentAccess.BODYWEIGHT:
            score -= 15

        if score >= 25:
            recommendations.append(
                WorkoutPlanRecommendation(
                    template_id=plan["id"],
                    name=plan["name"],
                    description=plan["description"],
                    match_score=min(score, 100),
                    match_reasons=reasons,
                    days_per_week=plan["days"],
                )
            )

    recommendations.sort(key=lambda x: x.match_score, reverse=True)
    return recommendations[:3]


def get_personalized_tips(profile: UserProfile) -> List[str]:
    """Generate personalized tips based on goals and profile."""
    tips = []
    goal = profile.primary_goal
    experience = profile.experience_level

    goal_tips = {
        ModelFitnessGoal.LOSE_WEIGHT: [
            "Focus on compound movements to maximize calorie burn",
            "Add 2-3 cardio sessions between weight training days",
            "Track your nutrition - a slight caloric deficit is key",
            "Stay consistent with your workouts for best results",
        ],
        ModelFitnessGoal.BUILD_MUSCLE: [
            "Prioritize progressive overload - increase weight or reps weekly",
            "Aim for 1.6-2.2g protein per kg of bodyweight daily",
            "Rest 2-3 minutes between heavy compound sets",
            "Get 7-9 hours of sleep for optimal recovery and growth",
        ],
        ModelFitnessGoal.GET_STRONGER: [
            "Focus on the big lifts: Squat, Bench, Deadlift, Overhead Press",
            "Train in the 3-5 rep range for main lifts",
            "Deload every 4-6 weeks to prevent burnout",
            "Perfect your form before adding more weight",
        ],
        ModelFitnessGoal.IMPROVE_ENDURANCE: [
            "Mix strength training with cardio sessions",
            "Try circuit training with minimal rest between exercises",
            "Gradually increase workout volume over time",
            "Focus on breathing techniques during exercise",
        ],
        ModelFitnessGoal.GENERAL_FITNESS: [
            "Balance strength, cardio, and flexibility training",
            "Aim for consistency over intensity",
            "Include mobility work in your routine",
            "Listen to your body and adjust intensity as needed",
        ],
        ModelFitnessGoal.TONE_UP: [
            "Combine resistance training with moderate cardio",
            "Focus on higher rep ranges (10-15) with controlled tempo",
            "Maintain a slight caloric deficit while keeping protein high",
            "Include both compound and isolation exercises",
        ],
        ModelFitnessGoal.BULK: [
            "Eat in a caloric surplus of 300-500 calories daily",
            "Focus on progressive overload each session",
            "Prioritize sleep for optimal recovery and growth",
            "Train each muscle group at least twice per week",
        ],
        ModelFitnessGoal.CUT: [
            "Maintain strength training to preserve muscle mass",
            "Add HIIT or steady-state cardio 2-4 times per week",
            "Keep protein intake high while in caloric deficit",
            "Monitor your progress with photos, not just the scale",
        ],
        ModelFitnessGoal.ATHLETIC_PERFORMANCE: [
            "Include explosive movements like jumps and throws",
            "Train movement patterns, not just muscles",
            "Focus on mobility and flexibility",
            "Balance strength work with sport-specific training",
        ],
        ModelFitnessGoal.FLEXIBILITY: [
            "Stretch after your workouts when muscles are warm",
            "Hold stretches for 30-60 seconds for best results",
            "Consider yoga or dedicated mobility sessions",
            "Be patient - flexibility gains take time",
        ],
    }

    if goal and goal in goal_tips:
        tips.extend(goal_tips[goal][:3])

    if experience == ModelExperienceLevel.BEGINNER:
        tips.append("Focus on learning proper form before increasing weight")
    elif experience == ModelExperienceLevel.INTERMEDIATE:
        tips.append("Consider tracking your workouts to monitor progress")
    elif experience == ModelExperienceLevel.ADVANCED:
        tips.append("Implement periodization to continue making progress")

    return tips[:5]


def get_goal_specific_advice(profile: UserProfile) -> str:
    """Get a summary advice paragraph for the user's goal."""
    goal = profile.primary_goal
    days = profile.training_days_per_week or 3

    advice_map = {
        ModelFitnessGoal.LOSE_WEIGHT: f"For weight loss with {days} training days, focus on full-body compound movements that burn more calories. Combine your weight training with moderate cardio on rest days. Remember, nutrition is key - aim for a slight caloric deficit while maintaining protein intake to preserve muscle mass.",
        ModelFitnessGoal.BUILD_MUSCLE: f"To build muscle with {days} days per week, prioritize progressive overload and adequate recovery. Each muscle group should be trained at least twice per week for optimal hypertrophy. Focus on compound movements first, then isolation exercises to target specific areas.",
        ModelFitnessGoal.GET_STRONGER: f"Building strength with {days} training days means focusing on the main compound lifts. Use lower rep ranges (3-5) with heavier weights and longer rest periods. Track your lifts and aim to add weight or reps each session for continuous progress.",
        ModelFitnessGoal.IMPROVE_ENDURANCE: f"Improving endurance with {days} days requires a mix of resistance training and cardiovascular work. Focus on higher rep ranges, shorter rest periods, and consider adding circuit-style training to build both muscular and cardiovascular endurance.",
        ModelFitnessGoal.GENERAL_FITNESS: f"With {days} days available, you can build a well-rounded fitness routine. Mix strength training with cardiovascular exercise and flexibility work throughout your week for balanced health benefits and sustainable progress.",
        ModelFitnessGoal.TONE_UP: f"To tone up with {days} training days, combine resistance training with a moderate caloric deficit. Focus on full-body workouts that target all major muscle groups, and include some cardio to help reveal muscle definition.",
        ModelFitnessGoal.BULK: f"For bulking with {days} days per week, focus on progressive overload with compound movements. Eat in a caloric surplus and prioritize protein intake. Your selected program will help you maximize muscle growth with adequate training frequency.",
        ModelFitnessGoal.CUT: f"During a cut with {days} training days, maintaining your strength training is crucial to preserve muscle mass. Keep intensity high but volume manageable, and add cardio as needed to create your caloric deficit.",
        ModelFitnessGoal.ATHLETIC_PERFORMANCE: f"For athletic performance with {days} days, balance strength training with sport-specific work. Focus on explosive movements, mobility, and functional fitness that transfers to your activities.",
        ModelFitnessGoal.FLEXIBILITY: f"With {days} training days focused on flexibility, combine resistance training with dedicated stretching and mobility work. Yoga or pilates can complement your routine for improved range of motion.",
    }

    return advice_map.get(
        goal,
        f"With {days} training days per week, we've selected programs that match your schedule and goals. Stay consistent, track your progress, and don't hesitate to adjust as you learn what works best for your body.",
    )
