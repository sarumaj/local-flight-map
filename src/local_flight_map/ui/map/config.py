from dataclasses import dataclass
from ...api.base import Location, BBox


@dataclass
class MapConfig:
    """Configuration for the map interface"""
    center: Location
    radius: float
    zoom_start: int = 12
    max_bounds: bool = True
    control_scale: bool = True
    provider: str = "adsbexchange"

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
