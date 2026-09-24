from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_base_url: str = "http://localhost:8000"
    api_timeout_seconds: float = 30

    mcp_host: str = "0.0.0.0"
    mcp_port: int = 9000


settings = Settings()
