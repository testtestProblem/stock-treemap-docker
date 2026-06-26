from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SJ_API_KEY: str
    SJ_SEC_KEY: str
    SJ_PRODUCTION: bool = True

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parents[3] / ".env"),
        env_file_encoding="utf-8",
    )


settings = Settings()
