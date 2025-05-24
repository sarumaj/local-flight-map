import folium
import panel as pn
import uvicorn
from panel.io.fastapi import add_applications
import fastapi
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging

from ...api.base import Location
from ...api import ApiClient
from .config import MapConfig
from .layers import MapLayers
from .data import DataSource


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")


class MapInterface:
    """Main interface for the flight map application"""

    def __init__(self, *, center: Location, radius: float = 50, client: ApiClient):
        self._config = MapConfig(center=center, radius=radius)
        self._client = client
        self._data = DataSource(client)

        # Setup FastAPI app
        self._app = fastapi.FastAPI()
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "HEAD", "OPTIONS"],
            allow_headers=["*"],
        )
        self._app.mount(
            "/ui/static",
            StaticFiles(directory=str(Path(__file__).parent / "static")),
            name="static"
        )
        self._app.add_api_route("/aircrafts", self.get_aircrafts_geojson, methods=["GET"])
        add_applications({"/": self.create_map_widget}, app=self._app, title="Local Flight Map")

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

    async def __aenter__(self):
        """Enter the async context manager"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager"""
        if hasattr(self._client, '__aexit__'):
            await self._client.__aexit__(exc_type, exc_val, exc_tb)

    async def get_aircrafts_geojson(self) -> JSONResponse:
        """API endpoint to get aircraft data"""
        try:
            aircrafts = await self._data.get_aircrafts_geojson(self._config)
            logger.info(f"Aircrafts: {len(aircrafts['features'])}")
            return JSONResponse(
                content=aircrafts,
                status_code=200
            )
        except Exception as e:
            logger.error(f"Error processing aircraft data: {e}")
            return JSONResponse(
                content={"error": str(e)},
                status_code=500
            )

    def create_map_widget(self):
        """Create the map widget for Panel"""
        return pn.pane.plot.Folium(self._map, sizing_mode="stretch_both")

    async def serve(self, port: int = 5006):
        """Start the server"""
        config = uvicorn.Config(self._app, host="localhost", port=port)
        server = uvicorn.Server(config)

        try:
            await server.serve()
        finally:
            if hasattr(self._client, 'close'):
                await self._client.close()
            elif hasattr(self._client, '__aexit__'):
                await self._client.__aexit__(None, None, None)
