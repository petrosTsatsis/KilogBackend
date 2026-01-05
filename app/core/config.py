from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str
    PROJECT_VERSION: str

    JWT_KEY: str
    CLERK_SECRET_KEY: str
    CLERK_WEBHOOK_SECRET: str

    DATABASE_URL: str

    # RESEND_API_KEY: str

    SUPABASE_URL: str
    SUPABASE_KEY: str

    ENVIRONMENT: str
    DEBUG: bool

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Instantiate global settings object
settings = Settings()
