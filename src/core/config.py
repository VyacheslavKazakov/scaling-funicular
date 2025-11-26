from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    listen_addr: str = "0.0.0.0"
    listen_port: int = 8008
    allowed_hosts: list[str] | tuple[str, str, str] = (
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
    )

    rate_limit: str = "100/minute"

    cache_host: str = "cachedb"
    cache_port: int = 6379
    cache_db: int = 1
    cache_ttl_in_seconds: int = 60
    cache_prefix: str = "sf"

    default_model: str = Field(default="gpt-5-mini", alias="MODEL")
    openai_api_key: str = Field(default="dummy", alias="KEY")
    default_temperature: float = 0.0
    default_max_tokens: int = 4096

    safe_execute_code_timeout_sec: int = 10
    question_max_length: int = 2048

    enable_metrics_variable_name: str = "ENABLE_METRICS"
    enable_tracing: bool = False

    workers: int = 1
    debug: bool = False
    log_level: str = "INFO"


settings = Settings()
