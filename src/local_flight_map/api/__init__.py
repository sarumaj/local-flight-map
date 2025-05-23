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
        # Initialize each client with the same config
        self._opensky_client = OpenSkyClient(config)
        self._hexdb_client = HexDbClient(config)
        self._adsbexchange_client = AdsbExchangeClient(config)

    async def __aenter__(self):
        """Enter the async context manager"""
        await self._opensky_client.__aenter__()
        await self._hexdb_client.__aenter__()
        await self._adsbexchange_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager"""
        await self._opensky_client.__aexit__(exc_type, exc_val, exc_tb)
        await self._hexdb_client.__aexit__(exc_type, exc_val, exc_tb)
        await self._adsbexchange_client.__aexit__(exc_type, exc_val, exc_tb)

    # Delegate methods to appropriate clients
    async def get_states_from_opensky(self, *args, **kwargs):
        return await self._opensky_client.get_states_from_opensky(*args, **kwargs)

    async def get_my_states_from_opensky(self, *args, **kwargs):
        return await self._opensky_client.get_my_states_from_opensky(*args, **kwargs)

    async def get_track_by_aircraft_from_opensky(self, *args, **kwargs):
        return await self._opensky_client.get_track_by_aircraft_from_opensky(*args, **kwargs)

    async def get_aircraft_information_from_hexdb(self, *args, **kwargs):
        return await self._hexdb_client.get_aircraft_information_from_hexdb(*args, **kwargs)

    async def get_airport_information_from_hexdb(self, *args, **kwargs):
        return await self._hexdb_client.get_airport_information_from_hexdb(*args, **kwargs)

    async def get_route_information_from_hexdb(self, *args, **kwargs):
        return await self._hexdb_client.get_route_information_from_hexdb(*args, **kwargs)

    async def get_aircraft_from_adsbexchange_by_registration(self, *args, **kwargs):
        return await self._adsbexchange_client.get_aircraft_from_adsbexchange_by_registration(*args, **kwargs)

    async def get_aircraft_from_adsbexchange_by_icao24(self, *args, **kwargs):
        return await self._adsbexchange_client.get_aircraft_from_adsbexchange_by_icao24(*args, **kwargs)

    async def get_aircraft_from_adsbexchange_by_callsign(self, *args, **kwargs):
        return await self._adsbexchange_client.get_aircraft_from_adsbexchange_by_callsign(*args, **kwargs)

    async def get_aircraft_from_adsbexchange_by_squawk(self, *args, **kwargs):
        return await self._adsbexchange_client.get_aircraft_from_adsbexchange_by_squawk(*args, **kwargs)

    async def get_military_aircrafts_from_adsbexchange(self, *args, **kwargs):
        return await self._adsbexchange_client.get_military_aircrafts_from_adsbexchange(*args, **kwargs)

    async def get_aircraft_from_adsbexchange_within_range(self, *args, **kwargs):
        return await self._adsbexchange_client.get_aircraft_from_adsbexchange_within_range(*args, **kwargs)


__all__ = [
    k for k, v in globals().items() if v in (
        ApiConfig,
        ApiClient,
        BBox,
        Location
    )
]
