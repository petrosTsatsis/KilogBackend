from datetime import date
from unittest.mock import Mock, MagicMock

import pytest

from app.core.exceptions import (
    PermissionDeniedException,
    ExerciseNotFoundException
)
from app.models import Workout
from app.schemas import WorkoutUpdate
from app.schemas.set_schema import SetCreate
from app.schemas.workout_schema import WorkoutCreate, WorkoutExerciseCreate
from app.services.workout_service import create_workout, get_workout_by_id, update_workout


@pytest.fixture
def mock_db():
    return Mock()


@pytest.fixture
def complex_workout_input():
    """
    Creates a payload: 1 Workout -> 1 Exercise -> 2 Sets
    """
    return WorkoutCreate(
        date=date.today(),
        notes="Heavy day",
        exercises=[
            WorkoutExerciseCreate(
                exercise_id=10,
                sets=[
                    SetCreate(weight=100, reps=5, rpe=8),
                    SetCreate(weight=100, reps=5, rpe=9)
                ]
            )
        ]
    )


def test_create_workout_success(mock_db, complex_workout_input):
    """
    Scenario: Happy path. Deep nested creation.
    We need to mock the exercise check passing.
    """
    # Arrange
    user_id = 1

    # Mock the 'get_exercise_by_id' check to pass quietly
    # We patch the import inside the service module
    with pytest.MonkeyPatch.context() as m:
        # Mocking the dependency function inside workout_service
        m.setattr("app.services.workout_service.get_exercise_by_id", Mock())

        # Simulate DB flushes assigning IDs
        def simulate_flush():
            # This is a bit abstract in mocks, but ensures flush is called
            pass

        mock_db.flush.side_effect = simulate_flush

        # Act
        result = create_workout(mock_db, complex_workout_input, user_id)

        # Assert
        # 1 Workout + 1 Link + 2 Sets = 4 adds
        assert mock_db.add.call_count == 4
        mock_db.commit.assert_called_once()
        assert result.notes == "Heavy day"


def test_create_workout_invalid_exercise(mock_db, complex_workout_input):
    """
    Scenario: User tries to log a workout using an exercise ID
    they don't have access to (e.g. someone else's custom exercise).
    """
    user_id = 1

    # Patch the validation to RAISE an error
    with pytest.MonkeyPatch.context() as m:
        mock_validator = Mock(side_effect=ExerciseNotFoundException(10))
        m.setattr("app.services.workout_service.get_exercise_by_id", mock_validator)

        # Act & Assert
        with pytest.raises(ExerciseNotFoundException):
            create_workout(mock_db, complex_workout_input, user_id)

        # Ensure we rolled back
        mock_db.rollback.assert_called()
        # Ensure we didn't commit a half-broken workout
        mock_db.commit.assert_not_called()


def test_get_workout_security_check(mock_db):
    """
    Scenario: User 1 tries to fetch User 2's workout.
    """
    user_id = 1
    owner_id = 2

    # DB returns a workout, but it belongs to User 2
    workout = Workout(id=5, user_id=owner_id)
    mock_db.scalar.return_value = workout

    with pytest.raises(PermissionDeniedException):
        get_workout_by_id(mock_db, workout_id=5, user_id=user_id)


def test_update_workout_success(mock_db):
    """
    Scenario: User changes notes and REPLACES the exercises.
    Verify old exercises are cleared and new ones added.
    """
    # Arrange
    user_id = 1

    # FIX: Use a MagicMock instead of a real Workout() class.
    # This prevents SQLAlchemy from interfering with our .exercises property.
    existing_workout = MagicMock()
    existing_workout.id = 5
    existing_workout.user_id = user_id
    existing_workout.notes = "Old Notes"

    # Set up the exercises mock specifically
    mock_exercises = MagicMock()
    existing_workout.exercises = mock_exercises

    mock_db.scalar.return_value = existing_workout

    # Input: New notes + 1 New Exercise
    update_input = WorkoutUpdate(
        notes="New Notes",
        exercises=[
            WorkoutExerciseCreate(exercise_id=10, sets=[SetCreate(weight=50, reps=10)])
        ]
    )

    # Mock the security check passing
    with pytest.MonkeyPatch.context() as m:
        m.setattr("app.services.workout_service.get_exercise_by_id", Mock())

        # Act
        result = update_workout(mock_db, 5, update_input, user_id)

    # Assert
    # 1. Notes updated (on our mock object)
    assert result.notes == "New Notes"

    # 2. Verify we wiped old data
    mock_exercises.clear.assert_called_once()

    # 3. Verify we added new data
    mock_exercises.append.assert_called()

    mock_db.commit.assert_called_once()
