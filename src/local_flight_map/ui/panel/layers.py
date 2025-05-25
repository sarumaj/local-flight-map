import folium
from folium.plugins import MousePosition, MiniMap, Fullscreen
from dataclasses import dataclass

from ..folium import Realtime, MarkerCluster
from .config import MapConfig


class MapLayers:
    """Map layers"""

    @dataclass
    class _Layers:
        world_imagery: folium.TileLayer
        opnvkarte: folium.TileLayer
        mouse_position: MousePosition
        layer_control: folium.LayerControl
        cluster_group: MarkerCluster
        minimap: MiniMap
        full_screen: Fullscreen

        @classmethod
        def from_scratch(cls) -> 'MapLayers._Layers':
            """Create a new instance from scratch"""
            return cls(**dict.fromkeys(cls.__annotations__.keys(), None))

    def __init__(self, map_instance: folium.Map, config: MapConfig):
        self._map = map_instance
        self._config = config
        self._initialize_layers()

    def _initialize_layers(self):
        """Initialize the layers"""
        if not hasattr(self, '_layers'):
            self._layers = MapLayers._Layers.from_scratch()

        self._layers.world_imagery = folium.TileLayer(
            name="World Imagery",
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr=(
                'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, '
                'GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
            )
        )
        self._layers.opnvkarte = folium.TileLayer(
            name="OPNVKarte",
            tiles='https://tileserver.memomaps.de/tilegen/{z}/{x}/{y}.png',
            attr=(
                'Map <a href="https://memomaps.de/">memomaps.de</a> '
                '<a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, map data &copy; '
                '<a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            )
        )

        # Initialize control layers
        self._layers.mouse_position = MousePosition(
            position="topright",
            separator=", ",
            empty_string="NaN",
            num_digits=20,
            prefix="Coordinates:",
            lat_formatter="function(num) {return L.Util.formatNum(num, 3) + '&deg;N';};",
            lng_formatter="function(num) {return L.Util.formatNum(num, 3) + '&deg;E';};",
        )
        self._layers.layer_control = folium.LayerControl()
        self._layers.cluster_group = MarkerCluster(
            name="Local Flights",
            control=False,
            showCoverageOnHover=False,
            spiderfyDistanceMultiplier=1.5,
            removeOutsideVisibleBounds=True,
            chunkedLoading=True,
        )
        self._layers.realtime = Realtime(
            container=self._layers.cluster_group,
            interval=self._config.map_refresh_interval,
            remove_missing=True,
        )
        self._layers.minimap = MiniMap(
            tiles=self._layers.opnvkarte,
            width="200",
            height="200",
            position="bottomright",
            zoom_level_offset=-3,
            toggle_display=True,
            zoom_level_fixed=12,
        )
        self._layers.full_screen = Fullscreen(
            position="topleft",
            title="Full Screen",
            title_cancel="Exit Full Screen",
            force_separate_button=True,
        )

    def add_to_map(self):
        """Add all layers to the map"""
        self._layers.opnvkarte.add_to(self._map)
        self._layers.world_imagery.add_to(self._map)
        self._layers.mouse_position.add_to(self._map)
        self._layers.cluster_group.add_to(self._map)
        self._layers.realtime.add_to(self._map)
        self._layers.minimap.add_to(self._map)
        self._layers.full_screen.add_to(self._map)
        self._layers.layer_control.add_to(self._map)
