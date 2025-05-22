from typing import Optional
from async_lru import alru_cache
from dataclasses import dataclass
from pydantic import Field

from .base import BaseClient, BaseConfig, ResponseObject


@dataclass
class AircraftInformation(ResponseObject):
    """
    Represents information about an aircraft.

    Attributes:
        ICAOTypeCode: The ICAO type code of the aircraft.
        Manufacturer: The manufacturer of the aircraft.
        ModeS: The Mode S code of the aircraft.
        OperatorFlagCode: The operator flag code of the aircraft.
        RegisteredOwners: The registered owners of the aircraft.
        Registration: The registration of the aircraft.
        Type: The type of the aircraft.
    """
    ICAOTypeCode: str
    Manufacturer: str
    ModeS: str
    OperatorFlagCode: str
    RegisteredOwners: str
    Registration: str
    Type: str


@dataclass
class RouteInformation(ResponseObject):
    """
    Represents information about a route.

    Attributes:
        flight: The flight number of the route.
        route: The route of the flight.
        update_time: The time of the update of the route in seconds since epoch (Unix time).
    """
    flight: str
    route: str
    updatetime: int


@dataclass
class AirportInformation(ResponseObject):
    """
    Represents information about an airport.

    Attributes:
        airport: The airport code of the airport.
        country_code: The country code of the airport.
        iata: The IATA code of the airport.
        icao: The ICAO code of the airport.
        latitude: The latitude of the airport.
        longitude: The longitude of the airport.
        region_name: The region name of the airport.
    """
    airport: str
    country_code: str
    iata: str
    icao: str
    latitude: float
    longitude: float
    region_name: str


class HexDbConfig(BaseConfig):
    """
    Config for the HexDB API.

    Attributes:
        hexdb_base_url: The base URL for the HexDB API.
    """
    hexdb_base_url: str = Field(
        default="https://hexdb.io/",
        description="The base URL for the HexDB API"
    )


class HexDbClient(BaseClient):
    """
    Client for the HexDB API.
    """
    def __init__(self, config: Optional[HexDbConfig] = None):
        config = config or HexDbConfig()
        BaseClient.__init__(
            self,
            config=config,
            base_url=config.hexdb_base_url
        )

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.get_aircraft_information_from_hexdb.cache_close()
        await self.get_airport_information_from_hexdb.cache_close()
        await self.get_route_information_from_hexdb.cache_close()
        await super(HexDbClient, self).__aexit__(exc_type, exc_val, exc_tb)

    @alru_cache(maxsize=1000)
    async def get_route_information_from_hexdb(
        self,
        callsign: str,
    ) -> Optional[RouteInformation]:
        """
        Get route information from HexDB.

        Args:
            callsign: The callsign of the aircraft.

        Returns:
            Optional[RouteInformation]: The route information.
        """
        async with self._session.get("/api/v1/route/icao/{callsign}".format(
            callsign=callsign.lower().strip()
        )) as response:
            data = await self._handle_response(response)
            return RouteInformation.from_dict(data) if data else None

    @alru_cache(maxsize=1000)
    async def get_airport_information_from_hexdb(
        self,
        icao24: str
    ) -> Optional[AirportInformation]:
        """
        Get airport information from HexDB.

        Args:
            icao24: The ICAO code of the airport.

        Returns:
            Optional[AirportInformation]: The airport information.
        """
        async with self._session.get("/api/v1/airport/icao/{icao24}".format(
            icao24=icao24.lower().strip()
        )) as response:
            data = await self._handle_response(response)
            return AirportInformation.from_dict(data) if data else None

    @alru_cache(maxsize=1000)
    async def get_aircraft_information_from_hexdb(
        self,
        icao24: str
    ) -> Optional[AircraftInformation]:
        """
        Get aircraft information from HexDB.

        Args:
            icao24: The ICAO code of the aircraft.

        Returns:
            Optional[AircraftInformation]: The aircraft information.
        """
        async with self._session.get("/api/v1/aircraft/icao/{icao24}".format(
            icao24=icao24.lower().strip()
        )) as response:
            data = await self._handle_response(response)
            return AircraftInformation.from_dict(data) if data else None
