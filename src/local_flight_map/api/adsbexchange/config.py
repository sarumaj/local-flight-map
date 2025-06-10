from pydantic import Field

from ..base import BaseConfig


class AdsbExchangeConfig(BaseConfig):
    """
    Configuration for the ADSB Exchange API client.

    Attributes:
        adsbexchange_base_url: The base URL for the ADSB Exchange API.
        adsbexchange_api_key: The API key for the ADSB Exchange API.
    """
    adsbexchange_base_url: str = Field(
        default="https://adsbexchange-com1.p.rapidapi.com/",
        description="The base URL for the ADSB Exchange API"
    )
    adsbexchange_feeder_url: str = Field(
        default="https://globe.adsbexchange.com/",
        description="The base URL for the ADSB Exchange feeder"
    )
    adsbexchange_api_key: str = Field(
        default="",
        description="The API key for the ADSB Exchange API",
        repr=False,
        exclude=True
    )
