"""
HexDB API module for the Local Flight Map application.
Provides classes and utilities for interacting with the HexDB API to fetch aircraft, route, and airport information.
"""

from typing import Optional, Dict, Any
from async_lru import alru_cache
from dataclasses import dataclass
from pydantic import Field

from .base import BaseClient, BaseConfig, ResponseObject


@dataclass
class AircraftInformation(ResponseObject):
    """
    Represents information about an aircraft from the HexDB API.

    This class stores detailed information about an aircraft, including its type,
    manufacturer, registration, and ownership details.

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

    def patch_geojson_properties(self, geojson: Dict[str, Any]) -> Dict[str, Any]:
        """
        Patch the properties of a GeoJSON feature with the aircraft information.

        This method updates the properties of a GeoJSON feature with the aircraft
        information, converting the field names to lowercase and using underscores
        for spaces.

        Args:
            geojson: The GeoJSON feature to patch.

        Returns:
            The patched GeoJSON feature with updated properties.
        """
        geojson["properties"] = geojson.get("properties", {})
        geojson["properties"].update({
            "icao_type_code": self.ICAOTypeCode,
            "manufacturer": self.Manufacturer,
            "mode_s": self.ModeS,
            "operator_flag_code": self.OperatorFlagCode,
            "registered_owners": self.RegisteredOwners,
            "registration": self.Registration,
            "type": self.Type
        })
        return geojson


@dataclass
class RouteInformation(ResponseObject):
    """
    Represents information about a flight route from the HexDB API.

    This class stores information about a flight's route, including the flight number,
    route details, and when the information was last updated.

    Attributes:
        flight: The flight number of the route.
        route: The route of the flight.
        updatetime: The time of the update of the route in seconds since epoch (Unix time).
    """
    flight: str
    route: str
    updatetime: int

    def patch_geojson_properties(self, geojson: Dict[str, Any]) -> Dict[str, Any]:
        """
        Patch the properties of a GeoJSON feature with the route information.

        This method updates the properties of a GeoJSON feature with the route
        information, converting the field names to lowercase and using underscores
        for spaces.

        Args:
            geojson: The GeoJSON feature to patch.

        Returns:
            The patched GeoJSON feature with updated properties.
        """
        geojson["properties"] = geojson.get("properties", {})
        geojson["properties"].update({
            "flight": self.flight,
            "route": self.route,
            "update_time": self.updatetime
        })
        return geojson


@dataclass
class AirportInformation(ResponseObject):
    """
    Represents information about an airport from the HexDB API.

    This class stores detailed information about an airport, including its location,
    codes, and region information.

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

    def to_geojson(self) -> Dict[str, Any]:
        """
        Convert the airport information to GeoJSON format.

        This method creates a GeoJSON feature representing the airport's location
        and properties.

        Returns:
            A GeoJSON feature containing the airport's location and properties.
        """
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude]
            },
            "properties": {
                "airport": self.airport,
                "country_code": self.country_code,
                "iata": self.iata,
                "icao": self.icao,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "region_name": self.region_name
            }
        }


class HexDbConfig(BaseConfig):
    """
    Configuration class for the HexDB API client.

    This class manages the configuration settings for connecting to the HexDB API,
    including the base URL and any authentication requirements.

    Attributes:
        hexdb_base_url: The base URL for the HexDB API.
    """
    hexdb_base_url: str = Field(
        default="https://hexdb.io/",
        description="The base URL for the HexDB API"
    )


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
        await super(HexDbClient, self).__aexit__(exc_type, exc_val, exc_tb)

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
