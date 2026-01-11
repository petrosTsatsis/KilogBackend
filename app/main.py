from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.core import exceptions, errors
from app.core.config import settings
from app.routers import webhooks, exercises, workouts, users, analytics, workout_plans

app = FastAPI(
    title="Kilog API", version="1.0.0", description="API for the Kilog service."
)

# Parse CORS origins from environment variable (comma-separated)
cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

# --- EXCEPTION HANDLERS REGISTRATION ---

# Specific ones first, generic ones last.
app.add_exception_handler(exceptions.ResourceNotFoundException, errors.resource_not_found_handler)
app.add_exception_handler(exceptions.ResourceConflictException, errors.resource_conflict_handler)
app.add_exception_handler(exceptions.BusinessRuleViolationException, errors.business_rule_handler)

# Fallback
app.add_exception_handler(exceptions.FitAppException, errors.app_exception_handler)

# --- ROUTERS ---
app.include_router(webhooks.router)
app.include_router(exercises.router, prefix="/api")
app.include_router(workouts.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(workout_plans.router, prefix="/api")


@app.get("/")
async def home() -> dict[str, str]:
    return {"message": "Welcome to Kilog."}
