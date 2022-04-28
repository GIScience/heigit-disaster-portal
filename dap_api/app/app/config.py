from functools import lru_cache
from typing import Optional, Dict, Any, List

from pydantic import BaseSettings, validator, PostgresDsn


class Settings(BaseSettings):
    PROJECT_NAME: str
    ADMIN_USER: str
    ADMIN_USER_SECRET: str
    API_V1_STR: str = "/api/v1"
    ORS_BACKEND_URL: str = "https://api.openrouteservice.org/v2"

    CREATE_EXAMPLE_DATA_ON_STARTUP: bool = False
    DEBUG: bool = False

    CORS_ORIGINS: List[str] = []
    CORS_ORIGINS_REGEX: str = ""

    SECRET: str = "This is secret"
    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "app"
    POSTGRES_TEST_SERVER: str = "localhost"
    POSTGRES_TEST_PORT: str = "5433"

    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True, always=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    class Config:
        env_file = "/.env"


@lru_cache
def get_settings():
    return Settings()


settings = Settings()
