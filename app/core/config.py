from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    version: str = "0.1.0"
    environment: str = "development"

    openai_api_key: str = ""
    openai_model_write: str = "gpt-4.1-nano"
    openai_model_vision: str = "gpt-4.1-mini"
    openai_model_image: str = "gpt-image-1"


    openai_temperature: float = 0.7
    openai_max_tokens: int = 1024



settings = Settings()
