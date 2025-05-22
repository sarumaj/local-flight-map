from typing import Optional

from .opensky import OpenSkyClient, OpenSkyConfig
from .hexdb import HexDbClient, HexDbConfig
from .adsbexchange import AdsbExchangeClient, AdsbExchangeConfig
from .base import BBox, Location


class ApiConfig(OpenSkyConfig, HexDbConfig, AdsbExchangeConfig):
    pass


class ApiClient(OpenSkyClient, HexDbClient, AdsbExchangeClient):
    def __init__(self, config: Optional[ApiConfig] = None):
        config = config or ApiConfig()
        OpenSkyClient.__init__(self, config)
        HexDbClient.__init__(self, config)
        AdsbExchangeClient.__init__(self, config)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super(ApiClient, self).__aexit__(exc_type, exc_val, exc_tb)


__all__ = [
    k for k, v in globals().items() if v in (
        ApiConfig,
        ApiClient,
        BBox,
        Location
    )
]
