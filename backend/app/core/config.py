from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    openai_api_key: str = ""
    agent_model: str = "gpt-5.4-nano"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/mediqare_db"
    upload_dir: str = "./uploads"
    max_upload_bytes: int = 20_000_000
    admin_api_key: str = ""
    cors_origins: list[str] = ["http://localhost:8081", "http://localhost:19006", "http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
