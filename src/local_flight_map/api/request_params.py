from typing import TypedDict, NamedTuple
import math


class Center(NamedTuple):
    latitude: float
    longitude: float


class BBox(NamedTuple):
    min_lat: float  # South
    max_lat: float  # North
    min_lon: float  # West
    max_lon: float  # East

    @classmethod
    def get_bbox_by_radius(cls, center: Center, radius: float) -> 'BBox':
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

        latitude_in_degrees = radius / 60
        longitude_in_degrees = radius / 60 / math.cos(math.radians(center.latitude))

        longitude_in_degrees = min(longitude_in_degrees, 180)

        return BBox(
            min_lat=max(center.latitude - latitude_in_degrees, -90),
            max_lat=min(center.latitude + latitude_in_degrees, 90),
            min_lon=max(center.longitude - longitude_in_degrees, -180),
            max_lon=min(center.longitude + longitude_in_degrees, 180)
        )


class StatesRequestParams(TypedDict):
    time: int
    icao24: str
    lamin: float
    lamax: float
    lomin: float
    lomax: float
    extended: int = 1


class MyStatesRequestParams(TypedDict):
    time: int
    icao24: str
    serials: str


class TrackRequestParams(TypedDict):
    icao24: str
    time: int
