from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    """
    Base configuration class for API clients.
    Uses pydantic for configuration management.
    """
    # HTTP timeout settings (in seconds)
    http_connect_timeout: float = Field(
        default=30.0,
        description="Connection timeout for HTTP requests in seconds"
    )
    http_total_timeout: float = Field(
        default=60.0,
        description="Total timeout for HTTP requests in seconds"
    )
    http_keepalive_timeout: float = Field(
        default=30.0,
        description="Keep-alive timeout for HTTP connections in seconds"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        frozen=True,
        extra="ignore",
        case_sensitive=False
    )
