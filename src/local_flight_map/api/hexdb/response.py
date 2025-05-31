"""
HexDB API module for the Local Flight Map application.
Provides classes and utilities for interacting with the HexDB API to fetch aircraft, route, and airport information.
"""

from typing import Dict, Any
from dataclasses import dataclass

from ..base import ResponseObject


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

    def enrich_geojson(self, geojson: Dict[str, Any], inplace: bool = False) -> Dict[str, Any]:
        """
        Enrich the properties of a GeoJSON feature with the aircraft information.

        This method enriches the GeoJSON feature with the aircraft information.

        Args:
            geojson: The GeoJSON feature to enrich.
            inplace: Whether to update the feature in place.

        Returns:
            The enriched GeoJSON feature.
        """
        properties = geojson.get("properties", {}).copy()
        properties.update({
            "icao_type_code": self.ICAOTypeCode,
            "manufacturer": self.Manufacturer,
            "mode_s": self.ModeS,
            "operator_flag_code": self.OperatorFlagCode,
            "registered_owners": self.RegisteredOwners,
            "registration": self.Registration,
            "type": self.Type
        })
        if inplace:
            geojson["properties"] = properties
            return geojson
        return {
            "type": geojson["type"],
            "geometry": geojson["geometry"],
            "properties": properties
        }


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

    def enrich_geojson(self, geojson: Dict[str, Any], inplace: bool = False) -> Dict[str, Any]:
        """
        Enrich the properties of a GeoJSON feature with the route information.

        This method enriches the GeoJSON feature with the route information.

        Args:
            geojson: The GeoJSON feature to enrich.
            inplace: Whether to update the feature in place.

        Returns:
            The enriched GeoJSON feature.
        """
        properties = geojson.get("properties", {}).copy()
        properties.update({
            "flight": self.flight,
            "route": self.route,
            "update_time": self.updatetime
        })
        if inplace:
            geojson["properties"] = properties
            return geojson
        return {
            "type": geojson["type"],
            "geometry": geojson["geometry"],
            "properties": properties
        }


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
