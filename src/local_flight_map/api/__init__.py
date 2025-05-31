"""
API module for the Local Flight Map application.
Provides interfaces for various flight data sources and their configuration.
"""

from typing import Optional

from .opensky import OpenSkyClient, OpenSkyConfig
from .hexdb import HexDbClient, HexDbConfig
from .adsbexchange import AdsbExchangeClient, AdsbExchangeConfig
from .base import BBox, Location


class ApiConfig(OpenSkyConfig, HexDbConfig, AdsbExchangeConfig):
    """
    Combined configuration class for all API clients.
    Inherits configuration from OpenSky, HexDB, and ADSBExchange.
    """


class ApiClient(OpenSkyClient, HexDbClient, AdsbExchangeClient):
    """
    Combined API client that provides access to multiple flight data sources.
    Inherits functionality from OpenSky, HexDB, and ADSBExchange clients.
    """

    def __init__(self, config: Optional[ApiConfig] = None):
        """
        Initialize the API client with optional configuration.

        Args:
            config: Optional configuration object. If not provided, a default configuration will be used.
        """
        config = config or ApiConfig()
        OpenSkyClient.__init__(self, config)
        HexDbClient.__init__(self, config)
        AdsbExchangeClient.__init__(self, config)

    async def __aenter__(self):
        """
        Enter the async context manager.
        Initializes all client connections.

        Returns:
            self: The initialized API client instance.
        """
        await OpenSkyClient.__aenter__(self)
        await HexDbClient.__aenter__(self)
        await AdsbExchangeClient.__aenter__(self)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the async context manager.
        Closes all client connections.

        Args:
            exc_type: The type of exception that was raised, if any.
            exc_val: The exception value that was raised, if any.
            exc_tb: The traceback of the exception, if any.
        """
        await OpenSkyClient.__aexit__(self, exc_type, exc_val, exc_tb)
        await HexDbClient.__aexit__(self, exc_type, exc_val, exc_tb)
        await AdsbExchangeClient.__aexit__(self, exc_type, exc_val, exc_tb)


__all__ = [
    k for k, v in globals().items() if v in (
        ApiConfig,
        ApiClient,
        BBox,
        Location
    )
]
