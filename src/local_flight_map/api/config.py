from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiConfig(BaseSettings):
    hexdb_base_url: str = Field(
        default="https://hexdb.io/api/v1",
        description="The base URL for the HexDB API"
    )
    opensky_base_url: str = Field(
        default="https://opensky-network.org/api",
        description="The base URL for the OpenSky API"
    )
    opensky_username: str = Field(
        default="",
        description="The username for the OpenSky API"
    )
    opensky_password: str = Field(
        default="",
        description="The password for the OpenSky API"
    )
    opensky_rate_limit_window_no_auth: int = Field(
        default=10,
        description="The rate limit window for the OpenSky API without authentication"
    )
    opensky_rate_limit_window_auth: int = Field(
        default=5,
        description="The rate limit window for the OpenSky API with authentication"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        frozen=True,
        extra="ignore",
        case_sensitive=False
    )
