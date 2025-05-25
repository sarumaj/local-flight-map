from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Literal

from ...api.base import Location, BBox


class MapConfig(BaseSettings):
    """
    Run the local flight map UI.
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
    data_provider: Literal["adsbexchange", "opensky"] = Field(
        default="adsbexchange",
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
        frozen=True,
        extra="ignore",
        case_sensitive=False,
        cli_parse_args=True,
        cli_prog_name="local-flight-map",
        cli_avoid_json=True,
        cli_kebab_case=True
    )

    @property
    def map_bbox(self) -> BBox:
        """Get the bounding box for the map"""
        return BBox.get_bbox_by_radius(self.map_center, self.map_radius)

    def get_map_bounds(self):
        """Get the map bounds as a list of coordinates"""
        return [
            [self.map_bbox.min_lat, self.map_bbox.min_lon],
            [self.map_bbox.max_lat, self.map_bbox.max_lon]
        ]
