"""
Map layers module for the Local Flight Map application.
Provides classes and utilities for managing map layers and controls.
"""

import folium
from folium.plugins import MousePosition, MiniMap, Fullscreen
from dataclasses import dataclass

from ..plugins import Realtime, MarkerCluster
from .config import MapConfig


class MapLayers:
    """
    Manages the layers and controls for the flight map.
    Handles initialization and management of map tiles, markers, and UI controls.
    """

    @dataclass
    class _Layers:
        """
        Internal class for storing map layer instances.

        Attributes:
            world_imagery: Tile layer for satellite imagery.
            opnvkarte: Tile layer for OpenStreetMap-based transportation map.
            mouse_position: Control showing current mouse coordinates.
            layer_control: Control for toggling layer visibility.
            cluster_group: Group for clustering aircraft markers.
            minimap: Small overview map in the corner.
            full_screen: Control for toggling fullscreen mode.
            realtime: Realtime layer for displaying live aircraft positions.
        """
        world_imagery: folium.TileLayer
        opnvkarte: folium.TileLayer
        mouse_position: MousePosition
        cluster_group: MarkerCluster
        minimap: MiniMap
        full_screen: Fullscreen
        realtime: Realtime
        layer_control: folium.LayerControl

        @classmethod
        def from_scratch(cls) -> 'MapLayers._Layers':
            """
            Create a new instance with all attributes set to None.

            Returns:
                A new _Layers instance with all attributes initialized to None.
            """
            return cls(**dict.fromkeys(cls.__annotations__.keys(), None))

    def __init__(self, map_instance: folium.Map, config: MapConfig):
        """
        Initialize the map layers.

        Args:
            map_instance: The Folium map instance to add layers to.
            config: The map configuration containing layer settings.
        """
        self._map = map_instance
        self._config = config
        self._initialize_layers()

    def _initialize_layers(self):
        """
        Initialize all map layers and controls.
        Sets up tile layers, marker clustering, and UI controls.
        """
        if not hasattr(self, '_layers'):
            self._layers = MapLayers._Layers.from_scratch()

        # Initialize tile layers
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
        self._layers.layer_control = folium.LayerControl(collapsed=False)
        self._layers.cluster_group = MarkerCluster(
            name="Local Flights",
            control=False,
            showCoverageOnHover=False,
            spiderfyDistanceMultiplier=1.5,
            removeOutsideVisibleBounds=False,
            chunkedLoading=True,
        )
        self._layers.realtime = Realtime(
            control=False,
            container=self._layers.cluster_group,
            interval=self._config.map_refresh_interval,
            remove_missing=True,
            start=True,
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
        """
        Add all layers and controls to the map.
        This method should be called after initialization to display the layers.
        """
        # Base tile layers first
        self._layers.opnvkarte.add_to(self._map)
        self._layers.world_imagery.add_to(self._map)

        # UI controls that don't depend on other layers
        self._layers.mouse_position.add_to(self._map)
        self._layers.minimap.add_to(self._map)
        self._layers.full_screen.add_to(self._map)

        # Marker cluster and realtime layer
        self._layers.cluster_group.add_to(self._map)
        self._layers.realtime.add_to(self._map)

        # Layer control last to ensure it can see all available layers
        self._layers.layer_control.add_to(self._map)
