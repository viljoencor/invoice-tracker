from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/invoicer"
    jwt_secret: str = "change-me"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 12

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()