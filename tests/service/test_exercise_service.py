from unittest.mock import Mock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import (
    ExerciseNotFoundException,
    PermissionDeniedException,
    DatabaseSystemException
)
from app.models import Exercise
from app.schemas.exercise_schema import ExerciseCreate, ExerciseBase
from app.services.exercise_service import (
    list_exercises,
    get_exercise_by_id,
    create_custom_exercise,
    update_exercise,
    delete_exercise
)


# --- FIXTURES ---

@pytest.fixture
def mock_db():
    return Mock()


@pytest.fixture
def user_id():
    return 1


# --- TEST GROUP 1: LIST EXERCISES ---

def test_list_exercises_returns_sequence(mock_db, user_id):
    """
    Scenario: Fetching exercises should return a combined list of
    System (None) and Custom (user_id) exercises.
    """
    # Arrange
    system_ex = Exercise(id=1, name="Bench Press")
    custom_ex = Exercise(id=2, name="My Glute Kickback", user_id=user_id)

    # Mock the chain: db.scalars(...).all()
    mock_db.scalars.return_value.all.return_value = [system_ex, custom_ex]

    # Act
    results = list_exercises(mock_db, user_id=user_id)

    # Assert
    assert len(results) == 2
    assert results[0].name == "Bench Press"
    # Verify the query was constructed (we can't easily check the WHERE clause on a mock,
    # but we verify the call happened)
    mock_db.scalars.assert_called_once()


def test_list_exercises_db_failure(mock_db, user_id):
    # Arrange
    mock_db.scalars.side_effect = SQLAlchemyError("Connection failed")

    # Act & Assert
    with pytest.raises(DatabaseSystemException):
        list_exercises(mock_db, user_id=user_id)


# --- TEST GROUP 2: GET EXERCISE (Read Security) ---

def test_get_exercise_success_system(mock_db, user_id):
    """
    Scenario: User can view a System exercise.
    """
    system_ex = Exercise(id=1, name="Squat")
    mock_db.scalar.return_value = system_ex

    result = get_exercise_by_id(mock_db, exercise_id=1, user_id=user_id)
    assert result.name == "Squat"


def test_get_exercise_success_own_custom(mock_db, user_id):
    """
    Scenario: User can view their own custom exercise.
    """
    custom_ex = Exercise(id=2, name="My Press", user_id=user_id)
    mock_db.scalar.return_value = custom_ex

    result = get_exercise_by_id(mock_db, exercise_id=2, user_id=user_id)
    assert result.id == 2


def test_get_exercise_fail_other_user(mock_db, user_id):
    """
    Scenario: User tries to view SOMEONE ELSE'S exercise.
    Expected: ExerciseNotFoundException (Privacy shielding).
    """
    other_user_id = 99
    # The DB finds it...
    private_ex = Exercise(id=3, name="Secret Move", user_id=other_user_id)
    mock_db.scalar.return_value = private_ex

    # ...but the Service blocks it.
    with pytest.raises(ExerciseNotFoundException):
        get_exercise_by_id(mock_db, exercise_id=3, user_id=user_id)


def test_get_exercise_not_found_real(mock_db, user_id):
    """
    Scenario: Exercise ID doesn't exist in DB.
    """
    mock_db.scalar.return_value = None

    with pytest.raises(ExerciseNotFoundException):
        get_exercise_by_id(mock_db, exercise_id=999, user_id=user_id)


# --- TEST GROUP 3: CREATE EXERCISE ---

def test_create_custom_exercise_success(mock_db, user_id):
    # Arrange
    ex_in = ExerciseCreate(name="New Move", category="Legs")

    # Simulate refresh populating the ID
    def simulate_refresh(obj):
        obj.id = 10

    mock_db.refresh.side_effect = simulate_refresh

    # Act
    result = create_custom_exercise(mock_db, ex_in, user_id)

    # Assert
    assert result.id == 10
    assert result.user_id == user_id  # Critical check: Assigned to current user
    assert result.name == "New Move"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


# --- TEST GROUP 4: UPDATE EXERCISE (Write Security) ---

def test_update_exercise_success_own(mock_db, user_id):
    """
    Scenario: User updates their own exercise.
    """
    # Arrange
    original_ex = Exercise(id=2, name="Old Name", category="Legs", user_id=user_id)
    mock_db.scalar.return_value = original_ex

    update_in = ExerciseBase(name="New Name", category="Legs")

    # Act
    result = update_exercise(mock_db, exercise_id=2, exercise_in=update_in, user_id=user_id)

    # Assert
    assert result.name == "New Name"
    mock_db.commit.assert_called_once()


def test_update_exercise_fail_system(mock_db, user_id):
    """
    Scenario: User tries to update a System exercise.
    Expected: PermissionDeniedException.
    """
    # Arrange
    system_ex = Exercise(id=1, name="Bench Press")
    mock_db.scalar.return_value = system_ex

    update_in = ExerciseBase(name="Hacked Press")

    # Act & Assert
    with pytest.raises(PermissionDeniedException) as exc:
        update_exercise(mock_db, 1, update_in, user_id)

    assert "User 1 does not have permission to access this System Exercises." in str(exc.value)
    mock_db.commit.assert_not_called()


def test_update_exercise_fail_other_user(mock_db, user_id):
    """
    Scenario: User tries to update someone else's exercise.
    Expected: PermissionDeniedException
    """
    other_user = 99
    private_ex = Exercise(id=5, name="Secret", user_id=other_user)
    mock_db.scalar.return_value = private_ex

    update_in = ExerciseBase(name="Hacked")

    with pytest.raises(PermissionDeniedException):
        update_exercise(mock_db, 5, update_in, user_id)


# --- TEST GROUP 5: DELETE EXERCISE (Write Security) ---

def test_delete_exercise_success_own(mock_db, user_id):
    # Arrange
    own_ex = Exercise(id=2, name="My Bad Exercise", user_id=user_id)
    mock_db.scalar.return_value = own_ex

    # Act
    delete_exercise(mock_db, exercise_id=2, user_id=user_id)

    # Assert
    mock_db.delete.assert_called_once_with(own_ex)
    mock_db.commit.assert_called_once()


def test_delete_exercise_fail_system(mock_db, user_id):
    """
    Scenario: User tries to delete a System exercise.
    Expected: PermissionDeniedException.
    """
    system_ex = Exercise(id=1, name="Bench Press")
    mock_db.scalar.return_value = system_ex

    with pytest.raises(PermissionDeniedException):
        delete_exercise(mock_db, exercise_id=1, user_id=user_id)

    mock_db.delete.assert_not_called()
