from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Kilog"
    PROJECT_VERSION: str = "0.1.0"

    # JWT_KEY: str
    # CLERK_SECRET_KEY: str
    # CLERK_WEBHOOK_SECRET: str

    DATABASE_URL: str

    # RESEND_API_KEY: str

    # SUPABASE_URL: str
    # SUPABASE_KEY: str

    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Instantiate global settings object
settings = Settings()
