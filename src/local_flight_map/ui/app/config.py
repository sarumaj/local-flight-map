"""
Configuration module for the Local Flight Map application.
Provides configuration classes and settings for the map interface.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Literal
import logging
from enum import Enum

from ...api.base import Location, BBox


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("local-flight-map")


class DataProvider(Enum):
    ADSBEXCHANGE = "adsbexchange"
    ADSBEXCHANGE_FEED = "adsbexchange_feed"
    OPENSKY = "opensky"
    OPENSKY_PERSONAL = "opensky_personal"


class MapConfig(BaseSettings):
    """
    Configuration class for the Local Flight Map application.
    Manages settings for the map display, data processing, and application behavior.

    Attributes:
        map_center: The center coordinates of the map.
        map_radius: The radius of the map in nautical miles.
        map_zoom_start: The initial zoom level of the map.
        map_max_bounds: Whether to restrict the map to maximum bounds.
        map_control_scale: Whether to display the scale control.
        map_refresh_interval: The interval between map updates in milliseconds.
        data_batch_size: The number of aircraft to process in each batch.
        data_max_threads: The maximum number of concurrent threads for data processing.
        data_provider: The source of aircraft data (adsbexchange, opensky, opensky_personal).
        app_port: The port number for the web application.
        app_dev_mode: Whether to run in development mode.
    """
    map_center: Location = Field(
        default_factory=lambda: Location(latitude=50.15, longitude=8.3166667),
        description="The center of the map"
    )
    map_radius: float = Field(
        default=50,
        description="The radius of the map"
    )
    map_zoom_start: int = Field(
        default=12,
        description="The zoom level of the map"
    )
    map_max_bounds: bool = Field(
        default=True,
        description="Whether to use max bounds"
    )
    map_control_scale: bool = Field(
        default=True,
        description="Whether to show the control scale"
    )
    map_refresh_interval: int = Field(
        default=200,
        description="The interval of the map refresh in milliseconds"
    )

    data_batch_size: int = Field(
        default=50,
        description="The batch size of the data"
    )
    data_max_threads: int = Field(
        default=10,
        description="The maximum number of threads to use for the data"
    )
    data_provider: Literal[
        DataProvider.ADSBEXCHANGE.value,
        DataProvider.ADSBEXCHANGE_FEED.value,
        DataProvider.OPENSKY.value,
        DataProvider.OPENSKY_PERSONAL.value
    ] = Field(
        default=DataProvider.ADSBEXCHANGE.value,
        description="The provider of the data",
    )

    app_port: int = Field(
        default=5006,
        description="The port of the app"
    )
    app_dev_mode: bool = Field(
        default=False,
        description="Whether to run in development mode"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        frozen=False,
        extra="ignore",
        case_sensitive=False,
        cli_parse_args=True,
        cli_prog_name="local-flight-map",
        cli_avoid_json=True,
        cli_kebab_case=True
    )

    @property
    def map_bbox(self) -> BBox:
        """
        Get the bounding box for the map.
        Calculates the bounding box based on the current center and radius.

        Returns:
            A BBox object representing the map's boundaries.
        """
        return BBox.get_bbox_by_radius(self.map_center, self.map_radius)

    @map_bbox.setter
    def map_bbox(self, bbox: BBox) -> None:
        """
        Set the bounding box for the map and update center and radius accordingly.
        Validates the bounding box and updates the map's center and radius.

        Args:
            bbox: The new bounding box to set.

        Raises:
            ValueError: If the bounding box is invalid.
        """
        bbox.validate()
        center, radius = bbox.to_center_and_radius()
        self.map_center = center
        self.map_radius = radius

    def get_map_bounds(self):
        """
        Get the map bounds as a list of coordinates.
        Returns the southwest and northeast corners of the map.

        Returns:
            A list containing two coordinate pairs:
            - [min_lat, min_lon]: The southwest corner
            - [max_lat, max_lon]: The northeast corner
        """
        return [
            [self.map_bbox.min_lat, self.map_bbox.min_lon],
            [self.map_bbox.max_lat, self.map_bbox.max_lon]
        ]
