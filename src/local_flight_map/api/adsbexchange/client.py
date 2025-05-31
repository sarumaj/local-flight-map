from typing import Optional
from urllib.parse import urlparse
from async_lru import alru_cache

from ..base import BaseClient, Location
from .config import AdsbExchangeConfig
from .response import AdsbExchangeResponse


class AdsbExchangeClient(BaseClient):
    """
    Client for interacting with the ADSB Exchange API.
    Provides methods for retrieving aircraft data using various search criteria.
    """

    def __init__(self, config: Optional[AdsbExchangeConfig] = None):
        """
        Initialize the ADSB Exchange client.

        Args:
            config: Optional configuration object. If not provided, a default configuration will be used.
        """
        config = config or AdsbExchangeConfig()
        BaseClient.__init__(
            self,
            config=config,
            base_url=config.adsbexchange_base_url,
            headers={
                'X-RapidAPI-Key': config.adsbexchange_api_key,
                'X-RapidAPI-Host': urlparse(config.adsbexchange_base_url).netloc
            }
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
        self.get_aircraft_from_adsbexchange_by_registration.cache_clear()
        self.get_aircraft_from_adsbexchange_by_icao24.cache_clear()
        self.get_aircraft_from_adsbexchange_by_callsign.cache_clear()
        self.get_aircraft_from_adsbexchange_by_squawk.cache_clear()
        self.get_military_aircrafts_from_adsbexchange.cache_clear()
        self.get_aircraft_from_adsbexchange_within_range.cache_clear()
        await BaseClient.__aexit__(self, exc_type, exc_val, exc_tb)

    @alru_cache(maxsize=1000)
    async def get_aircraft_from_adsbexchange_by_registration(
        self,
        registration: str
    ) -> Optional[AdsbExchangeResponse]:
        """
        Get aircraft data by registration number.

        Args:
            registration: The aircraft registration number.

        Returns:
            An AdsbExchangeResponse containing the aircraft data, or None if not found.
        """
        async with self._session.get(
            f"/v2/registration/{registration}",
        ) as response:
            data = await self._handle_response(response)
            return AdsbExchangeResponse.from_dict(data) if data else None

    @alru_cache(ttl=0.1)
    async def get_aircraft_from_adsbexchange_by_icao24(
        self,
        icao24: str
    ) -> Optional[AdsbExchangeResponse]:
        """
        Get aircraft data by ICAO24 address.

        Args:
            icao24: The ICAO24 address of the aircraft.

        Returns:
            An AdsbExchangeResponse containing the aircraft data, or None if not found.
        """
        async with self._session.get(
            f"/v2/icao/{icao24.lower().strip()}",
        ) as response:
            data = await self._handle_response(response)
            return AdsbExchangeResponse.from_dict(data) if data else None

    @alru_cache(ttl=0.1)
    async def get_aircraft_from_adsbexchange_by_callsign(
        self,
        callsign: str
    ) -> Optional[AdsbExchangeResponse]:
        """
        Get aircraft data by callsign.

        Args:
            callsign: The aircraft callsign.

        Returns:
            An AdsbExchangeResponse containing the aircraft data, or None if not found.
        """
        async with self._session.get(
            f"/v2/callsign/{callsign.lower().strip()}",
        ) as response:
            data = await self._handle_response(response)
            return AdsbExchangeResponse.from_dict(data) if data else None

    @alru_cache(ttl=0.1)
    async def get_aircraft_from_adsbexchange_by_squawk(
        self,
        squawk: str
    ) -> Optional[AdsbExchangeResponse]:
        """
        Get aircraft data by squawk code.

        Args:
            squawk: The aircraft squawk code.

        Returns:
            An AdsbExchangeResponse containing the aircraft data, or None if not found.
        """
        async with self._session.get(
            f"/v2/sqk/{squawk.strip()}",
        ) as response:
            data = await self._handle_response(response)
            return AdsbExchangeResponse.from_dict(data) if data else None

    @alru_cache(ttl=0.1)
    async def get_military_aircrafts_from_adsbexchange(
        self,
    ) -> Optional[AdsbExchangeResponse]:
        """
        Get data for all military aircraft.

        Returns:
            An AdsbExchangeResponse containing the military aircraft data, or None if not found.
        """
        async with self._session.get(
            "/v2/mil",
        ) as response:
            data = await self._handle_response(response)
            return AdsbExchangeResponse.from_dict(data) if data else None

    @alru_cache(ttl=0.1)
    async def get_aircraft_from_adsbexchange_within_range(
        self,
        center: Location,
        radius: int
    ) -> Optional[AdsbExchangeResponse]:
        """
        Get aircraft data within a specified range of a location.

        Args:
            center: The center location (latitude, longitude).
            radius: The radius in nautical miles.

        Returns:
            An AdsbExchangeResponse containing the aircraft data, or None if not found.
        """
        async with self._session.get(
            f"/v2/lat/{center.latitude:.6f}/lon/{center.longitude:.6f}/dist/{radius:.3f}",
        ) as response:
            data = await self._handle_response(response)
            return AdsbExchangeResponse.from_dict(data) if data else None
