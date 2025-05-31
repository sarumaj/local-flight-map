from typing import Optional
from async_lru import alru_cache

from ..base import BaseClient
from .config import HexDbConfig
from .response import AircraftInformation, AirportInformation, RouteInformation


class HexDbClient(BaseClient):
    """
    Client for interacting with the HexDB API.

    This class provides methods for fetching aircraft, route, and airport information
    from the HexDB API. It includes caching to improve performance and reduce API calls.

    The client supports:
    - Fetching aircraft information by ICAO24 code
    - Fetching route information by callsign
    - Fetching airport information by ICAO code
    - Automatic caching of responses
    - Proper cleanup of resources
    """
    def __init__(self, config: Optional[HexDbConfig] = None):
        """
        Initialize a new HexDB API client.

        Args:
            config: Optional configuration for the client. If not provided,
                   default configuration will be used.
        """
        config = config or HexDbConfig()
        BaseClient.__init__(
            self,
            config=config,
            base_url=config.hexdb_base_url
        )

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Clean up resources when exiting the async context.

        This method ensures that all cached data is properly cleared and
        connections are closed.

        Args:
            exc_type: The type of exception that was raised, if any.
            exc_val: The exception value that was raised, if any.
            exc_tb: The traceback of the exception, if any.
        """
        await self.get_aircraft_information_from_hexdb.cache_close()
        await self.get_airport_information_from_hexdb.cache_close()
        await self.get_route_information_from_hexdb.cache_close()
        await BaseClient.__aexit__(self, exc_type, exc_val, exc_tb)

    @alru_cache(maxsize=1000)
    async def get_route_information_from_hexdb(
        self,
        callsign: str,
    ) -> Optional[RouteInformation]:
        """
        Get route information from HexDB by callsign.

        This method fetches route information for a specific flight callsign.
        The response is cached to improve performance for repeated requests.

        Args:
            callsign: The callsign of the aircraft.

        Returns:
            Optional[RouteInformation]: The route information if found, None otherwise.
        """
        async with self._session.get(
            f"/api/v1/route/icao/{callsign.lower().strip()}"
        ) as response:
            data = await self._handle_response(response)
            return RouteInformation.from_dict(data) if data else None

    @alru_cache(maxsize=1000)
    async def get_airport_information_from_hexdb(
        self,
        icao24: str
    ) -> Optional[AirportInformation]:
        """
        Get airport information from HexDB by ICAO code.

        This method fetches detailed information about an airport using its ICAO code.
        The response is cached to improve performance for repeated requests.

        Args:
            icao24: The ICAO code of the airport.

        Returns:
            Optional[AirportInformation]: The airport information if found, None otherwise.
        """
        async with self._session.get(
            f"/api/v1/airport/icao/{icao24.lower().strip()}"
        ) as response:
            data = await self._handle_response(response)
            return AirportInformation.from_dict(data) if data else None

    @alru_cache(maxsize=1000)
    async def get_aircraft_information_from_hexdb(
        self,
        icao24: str
    ) -> Optional[AircraftInformation]:
        """
        Get aircraft information from HexDB by ICAO24 code.

        This method fetches detailed information about an aircraft using its ICAO24 code.
        The response is cached to improve performance for repeated requests.

        Args:
            icao24: The ICAO code of the aircraft.

        Returns:
            Optional[AircraftInformation]: The aircraft information if found, None otherwise.
        """
        async with self._session.get(
            f"/api/v1/aircraft/{icao24.lower().strip()}"
        ) as response:
            data = await self._handle_response(response)
            return AircraftInformation.from_dict(data) if data else None
