from dataclasses import dataclass

from ...api.base import Location, BBox


@dataclass
class MapConfig:
    """
    Configuration for the map interface

    Args:
        center: The center of the map
        radius: The radius of the map
        zoom_start: The zoom level of the map. Default is 12.
        max_bounds: Whether to use max bounds. Default is True.
        control_scale: Whether to show the control scale. Default is True.
        provider: The provider of the map. Default is "adsbexchange".
        port: The port of the map. Default is 5006.
        dev_mode: Whether to run in development mode. Default is False.
    """
    center: Location
    radius: float
    zoom_start: int = 12
    max_bounds: bool = True
    control_scale: bool = True
    provider: str = "adsbexchange"
    port: int = 5006
    dev_mode: bool = False

    @property
    def bbox(self) -> BBox:
        """Get the bounding box for the map"""
        return BBox.get_bbox_by_radius(self.center, self.radius)

    def get_map_bounds(self):
        """Get the map bounds as a list of coordinates"""
        return [
            [self.bbox.min_lat, self.bbox.min_lon],
            [self.bbox.max_lat, self.bbox.max_lon]
        ]
