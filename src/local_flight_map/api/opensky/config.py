from pydantic import Field

from ..base import BaseConfig


class OpenSkyConfig(BaseConfig):
    """
    Configuration class for the OpenSky Network API client.

    This class manages the configuration settings for connecting to the OpenSky
    Network API, including OAuth2 authentication and rate limiting parameters.

    Attributes:
        opensky_base_url: The base URL for the OpenSky API.
        opensky_auth_url: The URL for OAuth2 token endpoint.
        opensky_client_id: The OAuth2 client ID.
        opensky_client_secret: The OAuth2 client secret.
        opensky_rate_limit_window_no_auth: The rate limit window for the OpenSky API without authentication.
        opensky_rate_limit_window_auth: The rate limit window for the OpenSky API with authentication.
    """
    opensky_base_url: str = Field(
        default="https://opensky-network.org/",
        description="The base URL for the OpenSky API"
    )
    opensky_auth_url: str = Field(
        default="https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token",
        description="The URL for OAuth2 token endpoint"
    )
    opensky_client_id: str = Field(
        default="",
        description="The OAuth2 client ID"
    )
    opensky_client_secret: str = Field(
        default="",
        description="The OAuth2 client secret",
        repr=False,
        exclude=True
    )
    opensky_rate_limit_window_no_auth: int = Field(
        default=10,
        description="The rate limit window for the OpenSky API without authentication"
    )
    opensky_rate_limit_window_auth: int = Field(
        default=10,
        description="The rate limit window for the OpenSky API with authentication"
    )
