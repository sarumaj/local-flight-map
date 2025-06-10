from pydantic import Field

from ...base import BaseConfig


class AdsbExchangeFeederConfig(BaseConfig):
    """
    Configuration for the ADSB Exchange API client.

    Attributes:
        adsbexchange_base_url: The base URL for the ADSB Exchange API.
        adsbexchange_api_key: The API key for the ADSB Exchange API.
    """
    adsbexchange_feeder_base_url: str = Field(
        default="https://globe.adsbexchange.com/",
        description="The base URL for the ADSB Exchange API"
    )
    adsbexchange_feeder_uuid: str = Field(
        default="",
        description="The UUID for the ADSB Exchange feeder",
        repr=False,
        exclude=True
    )
