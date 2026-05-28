import os

from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    gateway_url: str = ""
    api_key: str = ""
    api_secret: str = ""

    model_config = SettingsConfigDict(
        env_file=(
            os.path.join(_PROJECT_ROOT, ".env"),
            os.path.join(_PROJECT_ROOT, ".env_dev"),
        ),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
