from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str
    PROJECT_VERSION: str

    JWT_KEY: str
    CLERK_SECRET_KEY: str
    CLERK_WEBHOOK_SECRET: str
    # Optional: Clerk frontend API for JWKS verification
    # e.g., "your-app.clerk.accounts.dev" - if not set, will be derived from CLERK_SECRET_KEY
    CLERK_FRONTEND_API: str = ""

    DATABASE_URL: str

    # RESEND_API_KEY: str

    SUPABASE_URL: str
    SUPABASE_KEY: str

    ENVIRONMENT: str
    DEBUG: bool

    # CORS configuration - comma-separated list of allowed origins
    CORS_ORIGINS: str = "http://localhost:5173, https://kilog-app.vercel.app/"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


# Instantiate global settings object
settings = Settings()
