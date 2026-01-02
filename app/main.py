from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.core import exceptions, errors

app = FastAPI(
    title="Kilog API", version="1.0.0", description="API for the Kilog service."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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


@app.get("/")
async def home() -> dict[str, str]:
    return {"message": "Welcome to Kilog."}
