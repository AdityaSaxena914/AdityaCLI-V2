from pydantic import Field, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProviderSettings(BaseModel):
    """Configuration for the active LLM provider."""
    default_provider: str = Field(
        default="lmstudio",
        description="Default LLM provider."
    )
    default_model: str = Field(
        default="qwen3.5",
        description="Default model identifier for the active provider."
    )


class LMStudioSettings(BaseModel):
    """Configuration for the LM Studio provider."""
    base_url: str = Field(
        default="http://127.0.0.1:1234/v1",
        description="Base URL of the LM Studio OpenAI-compatible API."
    )
    
    timeout: int = Field(
        default=60,
        description="Request timeout in seconds."
    )


class LoggingSettings(BaseModel):
    """Logging configuration"""
    level: str = Field(
        default="INFO",
        description="Default log level."
    )

    @property
    def log_level(self) -> int:
        """Return the python logging level"""

        import logging
        return getattr(logging, self.level.upper(), logging.INFO)
    


class Settings(BaseSettings):
    """Root configuration object for the AdityaCLI runtime."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    provider: ProviderSettings = ProviderSettings()
    lmstudio: LMStudioSettings = LMStudioSettings()
    logging: LoggingSettings = LoggingSettings()


settings = Settings()