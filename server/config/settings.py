from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "DNS_"}

    app_name: str = "Dead Network Society"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://dns_user:dns_password@localhost:5432/dead_network_society"

    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "llama3"

    agent_scheduler_interval_min: int = 30
    agent_scheduler_interval_max: int = 120


def get_settings() -> Settings:
    return Settings()
