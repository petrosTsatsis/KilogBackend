from datetime import datetime
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions import (
    UserAlreadyExistsException,
    UserNotFoundException,
    DatabaseSystemException
)
from app.models import User
from app.schemas.user_schema import UserCreate, UserUpdate
from app.services.user_service import create_user, get_user, get_user_details, update_user, delete_user


# --- FIXTURES ---

@pytest.fixture
def mock_db():
    """
    Returns a Mock object to simulate the SQLAlchemy Session.
    """
    return Mock()


@pytest.fixture
def user_input():
    return UserCreate(email="test@example.com", username="test_username", auth_id="auth0|12345")


# --- HELPERS ---

def simulate_refresh(obj):
    """
    Simulates SQLAlchemy refresh by assigning ID and created_at.
    """
    obj.id = 1
    obj.created_at = datetime.now()


# ====================================================================
# TEST GROUP 1: create_user
# ====================================================================

def test_create_user_success(mock_db, user_input):
    """
    Scenario: Happy path. User is created successfully.
    """
    # Arrange
    mock_db.refresh.side_effect = simulate_refresh

    # Act
    result = create_user(mock_db, user_input)

    # Assert
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

    assert result.id == 1
    assert result.email == user_input.email


def test_create_user_duplicate_auth_id(mock_db, user_input):
    """
    Scenario: Database rejects insert due to Auth ID constraint.
    Expected: Catch IntegrityError -> Raise UserAlreadyExistsException (Auth ID).
    """
    # Arrange
    # Simulate Postgres error structure: e.orig contains the driver message
    error = IntegrityError(None, None, None)
    error.orig = "Key (auth_id)=(auth0|12345) already exists."

    mock_db.commit.side_effect = error

    # Act & Assert
    with pytest.raises(UserAlreadyExistsException) as exc:
        create_user(mock_db, user_input)

    # Verify rollback happened
    mock_db.rollback.assert_called_once()
    assert "Auth ID" in str(exc.value)


def test_create_user_duplicate_email(mock_db, user_input):
    """
    Scenario: Database rejects insert due to Email constraint.
    Expected: Catch IntegrityError -> Raise UserAlreadyExistsException (Email).
    """
    # Arrange
    error = IntegrityError(None, None, None)
    error.orig = "Key (email)=(test@example.com) already exists."

    mock_db.commit.side_effect = error

    # Act & Assert
    with pytest.raises(UserAlreadyExistsException) as exc:
        create_user(mock_db, user_input)

    mock_db.rollback.assert_called_once()
    assert "Email" in str(exc.value)


def test_create_user_db_failure(mock_db, user_input):
    """
    Scenario: Critical DB failure (disk full, connection lost).
    Expected: Raise DatabaseSystemException.
    """
    # Arrange
    mock_db.commit.side_effect = SQLAlchemyError("Disk full")

    # Act & Assert
    with pytest.raises(DatabaseSystemException):
        create_user(mock_db, user_input)

    mock_db.rollback.assert_called_once()


# ====================================================================
# TEST GROUP 2: get_user
# ====================================================================

def test_get_user_found(mock_db):
    """
    Scenario: User exists.
    """
    # Arrange
    existing_user = User(id=1, email="found@test.com", username="test_username")
    mock_db.scalar.return_value = existing_user

    # Act
    result = get_user(mock_db, user_id=1)

    # Assert
    assert result.id == 1
    assert result.email == "found@test.com"


def test_get_user_not_found(mock_db):
    """
    Scenario: User ID does not exist.
    Expected: Raise UserNotFoundException.
    """
    # Arrange
    mock_db.scalar.return_value = None

    # Act & Assert
    with pytest.raises(UserNotFoundException):
        get_user(mock_db, user_id=99)


def test_get_user_db_error(mock_db):
    """
    Scenario: Database connection fails during read.
    """
    # Arrange
    mock_db.scalar.side_effect = SQLAlchemyError("Connection refused")

    # Act & Assert
    with pytest.raises(DatabaseSystemException):
        get_user(mock_db, user_id=1)


# ====================================================================
# TEST GROUP 3: get_user_details
# ====================================================================

def test_get_user_details_success(mock_db):
    """
    Scenario: Fetch user with eager loaded relationships.
    Note: We don't need to mock the complex .options() logic perfectly,
    we just verify that db.scalar returns the user when called.
    """
    # Arrange
    existing_user = User(id=1, email="details@test.com")
    mock_db.scalar.return_value = existing_user

    # Act
    result = get_user_details(mock_db, user_id=1)

    # Assert
    assert result.id == 1
    # Verify we actually ran a query (called scalar)
    mock_db.scalar.assert_called_once()


def test_get_user_details_not_found(mock_db):
    """
    Scenario: User ID missing when fetching details.
    """
    # Arrange
    mock_db.scalar.return_value = None

    # Act & Assert
    with pytest.raises(UserNotFoundException):
        get_user_details(mock_db, user_id=99)


def test_update_user_success(mock_db):
    # Arrange
    existing_user = User(id=1, email="old@test.com", role="USER")
    mock_db.scalar.return_value = existing_user

    # We want to update ONLY the email
    update_input = UserUpdate()

    # Act
    result = update_user(mock_db, user_id=1, user_in=update_input)

    # Assert
    assert result.email == "old@test.com"

    # Ensure role wasn't wiped out (thanks to exclude_unset=True)
    assert result.role == "USER"
    mock_db.commit.assert_called_once()


def test_update_last_login_timestamp(mock_db):
    """
    Scenario: System updates ONLY the last_login_at timestamp during login.
    """
    # Arrange
    existing_user = User(
        id=1,
        email="active@test.com",
        role="USER",
        last_login_at=datetime(2023, 1, 1)  # Old date
    )
    mock_db.scalar.return_value = existing_user

    # We simulate a new login happening NOW
    new_login_time = datetime.now()
    update_input = UserUpdate(last_login_at=new_login_time)

    # Act
    result = update_user(mock_db, user_id=1, user_in=update_input)

    # Assert
    assert result.last_login_at == new_login_time
    # Verify we didn't accidentally wipe out the email or role
    assert result.email == "active@test.com"
    assert result.role == "USER"

    mock_db.commit.assert_called_once()


def test_update_user_not_found(mock_db):
    mock_db.scalar.return_value = None
    update_input = UserUpdate()

    with pytest.raises(UserNotFoundException):
        update_user(mock_db, user_id=99, user_in=update_input)


def test_delete_user_success(mock_db):
    existing_user = User(id=1)
    mock_db.scalar.return_value = existing_user

    delete_user(mock_db, user_id=1)

    mock_db.delete.assert_called_once_with(existing_user)
    mock_db.commit.assert_called_once()
