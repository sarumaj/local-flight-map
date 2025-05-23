import folium
import panel as pn
import uvicorn
from panel.io.fastapi import add_applications

from ...api.base import Location
from ...api import ApiClient
from .config import MapConfig
from .layers import MapLayers
from .server import MapServer
from .data import MapData


class MapInterface:
    """Main interface for the flight map application"""

    def __init__(self, *, center: Location, radius: float = 50, client: ApiClient):
        self._config = MapConfig(center=center, radius=radius)
        self._client = client
        self._data = MapData(client)
        self._server = MapServer()

        # Initialize map
        self._map = folium.Map(
            location=(center.latitude, center.longitude),
            zoom_start=self._config.zoom_start,
            max_bounds=self._config.max_bounds,
            control_scale=self._config.control_scale,
            max_lat=self._config.bbox.max_lat,
            min_lat=self._config.bbox.min_lat,
            max_lon=self._config.bbox.max_lon,
            min_lon=self._config.bbox.min_lon,
        )

        # Set map bounds
        self._map.fit_bounds(self._config.get_map_bounds())
        self._map.options["radius"] = radius

        # Initialize and add layers
        self._layers = MapLayers(self._map, self._config.bbox)
        self._layers.add_to_map()
        self._layers.draw_bbox()

        # Setup server routes
        self._server.app.add_api_route("/aircrafts", self.get_aircrafts_geojson, methods=["GET"])

    async def __aenter__(self):
        """Enter the async context manager"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager"""
        if hasattr(self._client, '__aexit__'):
            await self._client.__aexit__(exc_type, exc_val, exc_tb)

    async def get_aircrafts_geojson(self):
        """API endpoint to get aircraft data"""
        return await self._data.get_aircrafts_geojson(
            Location(latitude=self._map.location[0], longitude=self._map.location[1]),
            self._map.options["radius"]
        )

    def create_map_widget(self):
        """Create the map widget for Panel"""
        return pn.pane.plot.Folium(self._map, sizing_mode="stretch_both")

    async def serve(self, port: int = 5006):
        """Start the server"""
        add_applications({"/map": self.create_map_widget}, app=self._server.app, title="Local Flight Map")
        config = uvicorn.Config(self._server.app, host="0.0.0.0", port=port)
        server = uvicorn.Server(config)

        try:
            await server.serve()
        finally:
            # Ensure client sessions are closed when server stops
            if hasattr(self._client, 'close'):
                await self._client.close()
            elif hasattr(self._client, '__aexit__'):
                await self._client.__aexit__(None, None, None)
