from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "auth-user-service"
    database_url: str = "postgresql+psycopg://postgres:postgres@postgres:5432/auth_db"
    firebase_project_id: str | None = None
    firebase_credentials_path: str | None = None
    auth_dev_mode: bool = True
    internal_api_key: str = "dev-internal-key"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
