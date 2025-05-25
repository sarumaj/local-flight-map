import aiohttp
from typing import Optional, NamedTuple, Dict, Any, List, Union, Tuple
import math
from dataclasses import asdict
import json
from itertools import zip_longest
from pydantic_settings import BaseSettings, SettingsConfigDict


class Location(NamedTuple):
    latitude: float
    longitude: float


class BBox(NamedTuple):
    min_lat: float  # South
    max_lat: float  # North
    min_lon: float  # West
    max_lon: float  # East

    def validate(self):
        """
        Validate the bounding box.

        Raises:
            ValueError: If the bounding box is invalid.
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
        Get a bounding box by a center and a radius.

        Args:
            center: The center of the bounding box in degrees (latitude, longitude)
            radius: The radius of the bounding box in nautical miles

        Returns:
            A BBox object

        Raises:
            ValueError: If radius is negative or if latitude is at the poles
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
        Convert the bounding box to a center and a radius.

        Returns:
            A tuple containing the center Location and radius in nautical miles.
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
    Base class for all response objects.
    """
    __annotations__: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResponseObject':
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
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'ResponseObject':
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def from_list(cls, data: List[Any]) -> 'ResponseObject':
        return cls.from_dict(dict(zip_longest(cls.__annotations__.keys(), data)))


class BaseConfig(BaseSettings):
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
    Base class for all API clients.
    """
    def __init__(self, config: Optional[BaseConfig] = None, **session_params: Dict[str, Any]):
        """
        Initialize the client.

        Args:
            config: The configuration to use for the client.
            session_params: Additional parameters for the session.
        """
        self._config = config or BaseConfig()
        self._session_params = session_params
        self._session = aiohttp.ClientSession(**self._session_params)

    async def close(self):
        """
        Close the client.
        """
        if self._session:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> 'BaseClient':
        """
        Enter the context manager.
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context manager.
        """
        _ = (exc_type, exc_val, exc_tb)
        await self.close()

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Optional[Any]:
        """
        Handle the response from the API.

        Args:
            response: The response from the API.

        Returns:
            The response from the API. None if the response is 404.

        Raises:
            aiohttp.ClientError: If the response is not successful.
        """
        if response.status == 404:
            return None

        response.raise_for_status()
        return await response.json() or None
