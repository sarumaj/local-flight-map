"""
API module for the Local Flight Map application.
Provides interfaces for various flight data sources and their configuration.
"""

from typing import NamedTuple

from .opensky import OpenSkyClient, OpenSkyConfig
from .hexdb import HexDbClient, HexDbConfig
from .adsbexchange import AdsbExchangeClient, AdsbExchangeConfig
from .adsbexchange.feed import AdsbExchangeFeederClient, AdsbExchangeFeederConfig
from .base import BBox, Location


class ApiConfig(OpenSkyConfig, HexDbConfig, AdsbExchangeConfig, AdsbExchangeFeederConfig):
    """
    Combined configuration class for all API clients.
    Inherits configuration from OpenSky, HexDB, and ADSBExchange.
    """


class ApiClients(NamedTuple):
    """
    Combined API client that provides access to multiple flight data sources.
    """
    opensky_client: OpenSkyClient
    hexdb_client: HexDbClient
    adsbexchange_client: AdsbExchangeClient
    adsbexchange_feed_client: AdsbExchangeFeederClient


__all__ = [
    k for k, v in globals().items() if v in (
        ApiConfig,
        ApiClients,
        OpenSkyClient,
        OpenSkyConfig,
        HexDbClient,
        HexDbConfig,
        AdsbExchangeClient,
        AdsbExchangeConfig,
        BBox,
        Location
    )
]
