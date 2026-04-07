from pydantic import Field

from ..base import BaseConfig


class JetPhotosConfig(BaseConfig):
    """
    Configuration class for the Jet Photos client.

    This class manages the configuration settings for connecting to the Jet Photos
    service, including authentication and rate limiting parameters.

    Attributes:
        jet_base_url: The base URL for the Jet Photos service.
    """

    jet_base_url: str = Field(default="https://jetphotos.com/", description="The base URL for the Jet Photos service")
