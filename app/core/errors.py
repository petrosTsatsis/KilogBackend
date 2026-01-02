# app/core/errors.py
import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    FitAppException,
    ResourceNotFoundException,
    ResourceConflictException,
    BusinessRuleViolationException
)

logger = logging.getLogger(__name__)


async def app_exception_handler(request: Request, exc: FitAppException):
    """
    Catch-all for any FitAppException we forgot to handle specifically.
    Default to 500, but structured.
    """
    logger.error(f"Unhandled App Exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal Error", "message": str(exc)},
    )


async def resource_not_found_handler(request: Request, exc: ResourceNotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "Not Found", "message": exc.message},
    )


async def resource_conflict_handler(request: Request, exc: ResourceConflictException):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"error": "Conflict", "message": str(exc)},
    )


async def business_rule_handler(request: Request, exc: BusinessRuleViolationException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Bad Request", "message": str(exc)},
    )
