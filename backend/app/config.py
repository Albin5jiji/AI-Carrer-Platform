from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Career Platform API"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://career_user:career_pass@localhost:5432/career_platform"
    jwt_secret_key: str = "change-this-secret-before-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    cors_origins: list[str] = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
    ]
    ai_enabled: bool = False
    ai_provider: str = "openai_compatible"
    ai_api_key: str = ""
    ai_model: str = "gpt-4o-mini"
    ai_base_url: str = "https://api.openai.com/v1"
    resume_storage_bucket: str = ""
    resume_storage_region: str = "us-east-1"
    resume_storage_endpoint: str | None = None
    resume_storage_prefix: str = "resumes"
    resume_presign_expiry_seconds: int = 900
    resume_max_file_size_bytes: int = 5 * 1024 * 1024

    # Creates any missing table on startup. Convenient for a fresh development database.
    # Existing databases should be upgraded with `alembic upgrade head` instead.
    auto_create_tables: bool = True

    # Loads the career reference dataset (role skill matrix, learning resources and
    # interview questions) the first time the API starts against an empty database.
    seed_reference_data: bool = True

    # AWS SDK credentials are standard environment variables consumed directly by boto3.
    # Ignore them here so provider configuration does not block application startup.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
