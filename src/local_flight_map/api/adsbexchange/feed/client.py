from typing import Optional
from async_lru import alru_cache

from ...base import BaseClient
from .config import AdsbExchangeFeederConfig
from .response import AdsbExchangeFeederResponse


class AdsbExchangeFeederClient(BaseClient):
    """
    Client for interacting with the ADSB Exchange Feeder.
    Provides methods for retrieving aircraft data.
    """

    def __init__(self, config: Optional[AdsbExchangeFeederConfig] = None):
        """
        Initialize the ADSB Exchange client.

        Args:
            config: Optional configuration object. If not provided, a default configuration will be used.
        """
        config = config or AdsbExchangeFeederConfig()
        BaseClient.__init__(
            self,
            config=config,
            base_url=config.adsbexchange_feeder_base_url,
        )

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the async context manager.
        Clears the LRU cache before closing.

        Args:
            exc_type: The type of exception that was raised, if any.
            exc_val: The exception value that was raised, if any.
            exc_tb: The traceback of the exception, if any.
        """
        self.get_aircraft_from_adsbexchange_feeder.cache_clear()
        await BaseClient.__aexit__(self, exc_type, exc_val, exc_tb)

    @alru_cache(ttl=0.1)
    async def get_aircraft_from_adsbexchange_feeder(
        self,
    ) -> Optional[AdsbExchangeFeederResponse]:
        """
        Get aircraft data from ADSB Exchange feeder.

        Returns:
            An AdsbExchangeFeederResponse containing the aircraft data, or None if not found.

        Raises:
            ValueError: If the ADSB Exchange feeder UUID is not set.
        """
        if not self._config.adsbexchange_feeder_uuid:
            raise ValueError("ADSB Exchange feeder UUID is not set")

        async with self._session.get(
            f"/uuid/?feed={self._config.adsbexchange_feeder_uuid}"
        ) as response:
            data = await self._handle_response(response)
            return AdsbExchangeFeederResponse.from_dict(data) if data else None
