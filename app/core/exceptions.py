# app/core/exceptions.py

class FitAppException(Exception):
    """Base class for all application logic errors."""
    pass


# =========================================================
# 1. SYSTEM & INFRASTRUCTURE ERRORS (Maps to HTTP 500)
# =========================================================
class DatabaseSystemException(FitAppException):
    """
    Raised when the database is unreachable or fails unexpectedly.
    The message usually contains the raw technical error (log only).
    """

    def __init__(self, original_error: str):
        super().__init__(f"System Database Error: {original_error}")


class AppIntegrityException(FitAppException):
    """
    Raised when a data consistency check fails (e.g., race conditions).
    """

    def __init__(self, detail: str):
        super().__init__(f"Integrity Error: {detail}")


# =========================================================
# 2. NOT FOUND ERRORS (Maps to HTTP 404)
# =========================================================
class ResourceNotFoundException(FitAppException):
    """Base for all 404-type errors."""

    def __init__(self, resource: str, id: int):
        self.message = f"{resource} with id {id} not found."
        super().__init__(self.message)


class UserNotFoundException(ResourceNotFoundException):
    def __init__(self, user_id: int):
        super().__init__(resource="User", id=user_id)


class WorkoutNotFoundException(ResourceNotFoundException):
    def __init__(self, workout_id: int):
        super().__init__(resource="Workout", id=workout_id)


class ExerciseNotFoundException(ResourceNotFoundException):
    def __init__(self, exercise_id: int):
        super().__init__(resource="Exercise", id=exercise_id)


class SetNotFoundException(ResourceNotFoundException):
    def __init__(self, set_id: int):
        super().__init__(resource="Set", id=set_id)


# =========================================================
# 3. CONFLICT ERRORS (Maps to HTTP 409)
# =========================================================
class ResourceConflictException(FitAppException):
    """Base for 409-type errors (duplicates, state conflicts)."""

    def __init__(self, message: str):
        super().__init__(message)


class UserAlreadyExistsException(ResourceConflictException):
    def __init__(self, identifier: str):
        super().__init__(f"User with identifier '{identifier}' already exists.")


# =========================================================
# 4. BUSINESS RULE & VALIDATION ERRORS (Maps to HTTP 400)
# =========================================================
class BusinessRuleViolationException(FitAppException):
    """Base for 400-type logic errors."""
    pass


class InvalidMetricException(BusinessRuleViolationException):
    """e.g., Negative weight or impossible reps."""

    def __init__(self, detail: str):
        super().__init__(f"Invalid metric value: {detail}")


class EmptyWorkoutException(BusinessRuleViolationException):
    """Raised if trying to save a workout with no exercises."""

    def __init__(self):
        super().__init__("Cannot save an empty workout. Add at least one exercise.")


# =========================================================
# 5. AUTHORIZATION ERRORS (Maps to HTTP 403)
# =========================================================
class PermissionDeniedException(FitAppException):
    """
    Raised when a user tries to access/modify a resource they don't own.
    """

    def __init__(self, resource: str, user_id: int):
        super().__init__(f"User {user_id} does not have permission to access this {resource}.")
