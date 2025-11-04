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
    secret_key: str = "50ae6b6f23a914d61c65b7bf6124107d73b47e0303c4da828c06092d1a18b056"

    default_model: str = Field(default="gpt-5-mini", alias="MODEL")
    openai_api_key: str = Field(default="dummy", alias="KEY")
    default_temperature: float = 0.0
    default_max_tokens: int = 4096

    default_prompt: str = "You are a helpful assistant. Answer the user's math question. Only answer, no comments."

    debug: bool = False
    log_level: str = "INFO"


settings = Settings()
