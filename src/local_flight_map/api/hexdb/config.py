from pydantic import Field

from ..base import BaseConfig


class HexDbConfig(BaseConfig):
    """
    Configuration class for the HexDB API client.

    This class manages the configuration settings for connecting to the HexDB API,
    including the base URL and any authentication requirements.

    Attributes:
        hexdb_base_url: The base URL for the HexDB API.
    """
    hexdb_base_url: str = Field(
        default="https://hexdb.io/",
        description="The base URL for the HexDB API"
    )
