from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class OpenSkyConfig(BaseSettings):
    opensky_base_url: str = Field(default="https://opensky-network.org/api", description="The base URL for the OpenSky API")
    opensky_username: str = Field(default="", description="The username for the OpenSky API")
    opensky_password: str = Field(default="", description="The password for the OpenSky API")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        frozen=True,
        extra="ignore",
        case_sensitive=False
    )
