"""
Base module for the API package.
Provides base classes and utilities for API clients and data structures.
"""

from typing import NamedTuple, Tuple
import math


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
