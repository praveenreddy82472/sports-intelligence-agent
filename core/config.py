from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # === Application Info ===
    app_name: str = "Global Sports Intelligence Agent"
    environment: str | None = "development"

    # === API Keys ===
    openai_api_key: str | None = None
    azure_openai_endpoint :str | None = None
    sports_api_key: str | None = None
    weather_api_key: str | None = None
    azure_maps_key: str | None = None

    # === Optional Config ===
    azure_region: str | None = "eastus"
    log_level: str | None = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore any additional env vars


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

if __name__ == "__main__":
    print("✅ Loaded configuration:")
    print(settings.model_dump())
