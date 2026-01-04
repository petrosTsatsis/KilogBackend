from datetime import date
from unittest.mock import Mock

import pytest

from app.core.exceptions import DatabaseSystemException
from app.services.analytics_service import get_personal_best, get_exercise_progress


@pytest.fixture
def mock_db():
    return Mock()


def test_get_personal_best_calls_db(mock_db):
    """
    Verifies that the function constructs a query and executes it.
    """
    user_id = 1
    exercise_id = 10

    # Simulate DB returning a max weight of 100.0
    mock_db.scalar.return_value = 100.0

    result = get_personal_best(mock_db, user_id, exercise_id)

    assert result == 100.0
    mock_db.scalar.assert_called_once()
    # We can inspect the string representation of the call args if we really want to debug the SQL
    # , but primarily we ensure the DB was hit.


def test_get_exercise_progress_formatting(mock_db):
    """
    Verifies that the raw DB rows are converted to a clean dictionary format.
    """
    user_id = 1
    exercise_id = 10

    # Mocking a Row object (which usually has .date and .top_weight attributes)
    row_1 = Mock(date=date(2023, 1, 1), top_weight=80.0)
    row_2 = Mock(date=date(2023, 1, 5), top_weight=85.0)

    mock_db.execute.return_value.all.return_value = [row_1, row_2]

    data = get_exercise_progress(mock_db, user_id, exercise_id)

    assert len(data) == 2
    assert data[0]["weight"] == 80.0
    assert data[1]["date"] == date(2023, 1, 5)


def test_analytics_db_error(mock_db):
    # Simulate a DB crash
    from sqlalchemy.exc import SQLAlchemyError
    mock_db.scalar.side_effect = SQLAlchemyError("Query failed")

    with pytest.raises(DatabaseSystemException):
        get_personal_best(mock_db, 1, 1)
