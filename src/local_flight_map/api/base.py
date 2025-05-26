"""
Base module for the API package.
Provides base classes and utilities for API clients and data structures.
"""

import aiohttp
from typing import Optional, NamedTuple, Dict, Any, List, Union, Tuple
import math
from dataclasses import asdict
import json
from itertools import zip_longest
from pydantic_settings import BaseSettings, SettingsConfigDict


class Location(NamedTuple):
    """
    Represents a geographical location with latitude and longitude.

    Attributes:
        latitude: The latitude in degrees (-90 to 90)
        longitude: The longitude in degrees (-180 to 180)
    """
    latitude: float
    longitude: float

    def validate(self):
        """
        Validate the location coordinates.

        Raises:
            ValueError: If the latitude or longitude is out of valid range
        """
        if -90 > self.latitude or self.latitude > 90:
            raise ValueError(f"Invalid latitude value: {self.latitude}")
        if -180 > self.longitude or self.longitude > 180:
            raise ValueError(f"Invalid longitude value: {self.longitude}")
        
    def get_angle_to(self, target: 'Location') -> float:
        """
        Calculate the initial bearing (angle) in degrees from this location to the target location.
        This uses the great circle formula to calculate the initial bearing between two points.
        
        Args:
            target: The target Location to calculate the angle to
            
        Returns:
            float: The initial bearing in degrees (0-360) where:
                  - 0 degrees points to true north
                  - 90 degrees points east
                  - 180 degrees points south
                  - 270 degrees points west
        """
        # Convert to radians
        lat_self = math.radians(self.latitude)
        lon_self = math.radians(self.longitude)
        lat_target = math.radians(target.latitude)
        lon_target = math.radians(target.longitude)
        
        # Calculate the bearing using the great circle formula
        diff_lon = lon_target - lon_self
        y = math.sin(diff_lon) * math.cos(lat_target)
        x = math.cos(lat_self) * math.sin(lat_target) - math.sin(lat_self) * math.cos(lat_target) * math.cos(diff_lon)
        bearing = math.degrees(math.atan2(y, x))
        
        # Normalize to 0-360 degrees
        return (bearing + 360) % 360

class BBox(NamedTuple):
    """
    Represents a bounding box with minimum and maximum latitude and longitude.

    Attributes:
        min_lat: The minimum latitude (south boundary)
        max_lat: The maximum latitude (north boundary)
        min_lon: The minimum longitude (west boundary)
        max_lon: The maximum longitude (east boundary)
    """
    min_lat: float  # South
    max_lat: float  # North
    min_lon: float  # West
    max_lon: float  # East

    def validate(self):
        """
        Validate the bounding box coordinates.

        Raises:
            ValueError: If any coordinate is out of valid range or if min values are greater than max values.
        """
        if 90 < self.min_lat or self.min_lat < -90:
            raise ValueError(f"Invalid latitude value: {self.min_lat}")
        if 90 < self.max_lat or self.max_lat < -90:
            raise ValueError(f"Invalid latitude value: {self.max_lat}")
        if 180 < self.min_lon or self.min_lon < -180:
            raise ValueError(f"Invalid longitude value: {self.min_lon}")
        if 180 < self.max_lon or self.max_lon < -180:
            raise ValueError(f"Invalid longitude value: {self.max_lon}")
        if self.min_lat >= self.max_lat:
            raise ValueError(f"min_lat must be less than max_lat: {self.min_lat} >= {self.max_lat}")
        if self.min_lon >= self.max_lon:
            raise ValueError(f"min_lon must be less than max_lon: {self.min_lon} >= {self.max_lon}")

    @classmethod
    def get_bbox_by_radius(cls, center: Location, radius: float) -> 'BBox':
        """
        Calculate a bounding box from a center point and radius.

        Args:
            center: The center location (latitude, longitude)
            radius: The radius in nautical miles

        Returns:
            A BBox object representing the calculated bounding box

        Raises:
            ValueError: If radius is negative or if center is too close to the poles
        """
        if radius < 0:
            raise ValueError("Radius must be non-negative")

        if abs(center.latitude) > 89.9:
            raise ValueError("Cannot calculate bounding box near the poles")

        latitude_skew = math.cos(math.radians(center.latitude))
        latitude_in_degrees = radius / 60
        longitude_in_degrees = radius / 60 / latitude_skew

        longitude_in_degrees = min(longitude_in_degrees, 180)

        return BBox(
            min_lat=max(center.latitude - latitude_in_degrees, -90),
            max_lat=min(center.latitude + latitude_in_degrees, 90),
            min_lon=max(center.longitude - longitude_in_degrees, -180),
            max_lon=min(center.longitude + longitude_in_degrees, 180)
        )

    def to_center_and_radius(self) -> Tuple[Location, float]:
        """
        Convert the bounding box to a center point and radius.

        Returns:
            A tuple containing:
                - Location: The center point of the bounding box
                - float: The radius in nautical miles
        """
        center = Location(
            latitude=(self.min_lat + self.max_lat) / 2,
            longitude=(self.min_lon + self.max_lon) / 2
        )

        latitude_skew = math.cos(math.radians(center.latitude))
        latitude_radius = (self.max_lat - self.min_lat) / 2 * 60
        longitude_radius = (self.max_lon - self.min_lon) / 2 * 60 * latitude_skew

        radius = max(latitude_radius, longitude_radius)

        return center, radius


class ResponseObject:
    """
    Base class for API response objects.
    Provides methods for converting between different data formats.
    """
    __annotations__: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the object to a dictionary.

        Returns:
            A dictionary representation of the object
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResponseObject':
        """
        Create an object from a dictionary.

        Args:
            data: The dictionary to create the object from

        Returns:
            A new ResponseObject instance
        """
        defaults = {}
        for field_name, field_type in cls.__annotations__.items():
            if hasattr(field_type, "__origin__"):
                if field_type.__origin__ is Union:
                    try:
                        defaults[field_name] = field_type.__args__[1]()
                    except Exception:
                        defaults[field_name] = None
                elif field_type.__origin__ is Union:
                    defaults[field_name] = None
        defaults.update(data)
        return cls(**defaults)

    def to_json(self) -> str:
        """
        Convert the object to a JSON string.

        Returns:
            A JSON string representation of the object
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'ResponseObject':
        """
        Create an object from a JSON string.

        Args:
            json_str: The JSON string to create the object from

        Returns:
            A new ResponseObject instance
        """
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def from_list(cls, data: List[Any]) -> 'ResponseObject':
        """
        Create an object from a list of values.

        Args:
            data: The list of values to create the object from

        Returns:
            A new ResponseObject instance
        """
        return cls.from_dict(dict(zip_longest(cls.__annotations__.keys(), data)))


class BaseConfig(BaseSettings):
    """
    Base configuration class for API clients.
    Uses pydantic for configuration management.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        frozen=True,
        extra="ignore",
        case_sensitive=False
    )


class BaseClient:
    """
    Base class for API clients.
    Provides common functionality for making HTTP requests and managing sessions.
    """
    def __init__(self, config: Optional[BaseConfig] = None, **session_params: Dict[str, Any]):
        """
        Initialize the API client.

        Args:
            config: Optional configuration object
            session_params: Additional parameters for the aiohttp session
        """
        self._config = config or BaseConfig()
        self._session_params = session_params
        self._session = aiohttp.ClientSession(**self._session_params)

    async def close(self):
        """
        Close the client's HTTP session.
        """
        if self._session:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> 'BaseClient':
        """
        Enter the async context manager.

        Returns:
            self: The initialized client instance
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the async context manager.
        Closes the HTTP session.

        Args:
            exc_type: The type of exception that was raised, if any
            exc_val: The exception value that was raised, if any
            exc_tb: The traceback of the exception, if any
        """
        _ = (exc_type, exc_val, exc_tb)
        await self.close()

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Optional[Any]:
        """
        Handle an HTTP response from the API.

        Args:
            response: The HTTP response to handle

        Returns:
            The parsed JSON response, or None if the response was 404

        Raises:
            aiohttp.ClientError: If the response indicates an error
        """
        if response.status == 404:
            return None

        response.raise_for_status()
        return await response.json() or None
