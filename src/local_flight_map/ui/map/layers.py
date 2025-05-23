import folium
from typing import Dict, Any
from folium.plugins import MousePosition, MiniMap

from ..folium.realtime import Realtime
from ..folium.markercluser import MarkerCluster
from ...api.base import BBox


class MapLayers:
    def __init__(self, map_instance: folium.Map, bbox: BBox):
        self._map = map_instance
        self._bbox = bbox
        self._layers: Dict[str, Any] = {}
        self._initialize_layers()

    def _initialize_layers(self):
        # Initialize base layers
        self._layers['world_imagery'] = folium.TileLayer(
            name="World Imagery",
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr=(
                'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, '
                'GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
            )
        )
        self._layers['opnvkarte'] = folium.TileLayer(
            name="OPNVKarte",
            tiles='https://tileserver.memomaps.de/tilegen/{z}/{x}/{y}.png',
            attr=(
                'Map <a href="https://memomaps.de/">memomaps.de</a> '
                '<a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, map data &copy; '
                '<a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            )
        )

        # Initialize control layers
        self._layers['mouse_position'] = MousePosition(
            position="topright",
            separator=", ",
            empty_string="NaN",
            num_digits=20,
            prefix="Coordinates:",
            lat_formatter="function(num) {return L.Util.formatNum(num, 3) + '&deg;N';};",
            lng_formatter="function(num) {return L.Util.formatNum(num, 3) + '&deg;E';};",
        )
        self._layers['layer_control'] = folium.LayerControl()
        self._layers['cluster_group'] = MarkerCluster(
            control=False,
            spiderfyOnMaxZoom=True,
            showCoverageOnHover=False,
            zoomToBoundsOnClick=True,
            disableClusteringAtZoom=16
        )
        self._layers['realtime'] = Realtime(
            container=self._layers['cluster_group'],
            interval=100,
        )
        self._layers['minimap'] = MiniMap(
            tiles=self._layers['opnvkarte'],
            width="200",
            height="200",
            position="bottomright",
            zoom_level_offset=-3,
            toggle_display=True,
            zoom_level_fixed=12,
        )

    def add_to_map(self):
        """Add all layers to the map"""
        self._layers['opnvkarte'].add_to(self._map)
        self._layers['world_imagery'].add_to(self._map)
        self._layers['mouse_position'].add_to(self._map)
        self._layers['cluster_group'].add_to(self._map)
        self._layers['realtime'].add_to(self._layers['cluster_group'])
        self._layers['minimap'].add_to(self._map)
        self._layers['layer_control'].add_to(self._map)

    def draw_bbox(self):
        """Draw the bounding box on the map"""
        folium.PolyLine(
            locations=[
                (self._bbox.min_lat, self._bbox.min_lon),
                (self._bbox.min_lat, self._bbox.max_lon),
                (self._bbox.max_lat, self._bbox.max_lon),
                (self._bbox.max_lat, self._bbox.min_lon),
                (self._bbox.min_lat, self._bbox.min_lon),
            ],
            color="red",
            weight=2,
            opacity=0.7
        ).add_to(self._map)

    @property
    def cluster_group(self):
        return self._layers['cluster_group']

    @property
    def realtime(self):
        return self._layers['realtime']
