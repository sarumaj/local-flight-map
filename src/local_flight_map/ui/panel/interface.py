import folium
import panel as pn
import uvicorn
from panel.io.fastapi import add_applications
import fastapi
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
import secrets
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from typing import Callable, Union, Dict, Any
import re
import time
import signal
import asyncio
from types import FrameType

from ...api import ApiClient
from .config import MapConfig
from .layers import MapLayers
from .data import DataSource
from .config import BBox


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("local-flight-map")


class MapInterface:
    """Main interface for the flight map application"""

    class EmptyFeatureCollection(JSONResponse):
        """Empty feature collection"""
        def __init__(self, **kwargs: Dict[str, Any]):
            JSONResponse.__init__(
                self,
                **{
                    "content": {
                        "type": "FeatureCollection",
                        "features": []
                    },
                    "status_code": 200,
                    **kwargs
                }
            )

    class SessionAuthenticator(BaseHTTPMiddleware):
        """Session authenticator"""
        def __init__(self, app: fastapi.FastAPI, paths: Dict[re.Pattern, Response] = None):
            """
            Initialize the session authenticator

            Args:
                app: The FastAPI app
                paths: Dictionary mapping regex patterns to responses for path-based authentication
            """
            BaseHTTPMiddleware.__init__(self, app)
            self._paths = paths

        async def dispatch(self, request: Request, call_next: Callable) -> fastapi.Response:
            if self._paths is not None:
                for path, response in self._paths.items():
                    if path.match(request.url.path):
                        if "authenticated" not in request.session:
                            request.session["authenticated"] = True
                            return response
            return await call_next(request)

    class RequestLoggerMiddleware(BaseHTTPMiddleware):
        """Request logger middleware"""
        def __init__(self, app: fastapi.FastAPI):
            """Initialize the request logger middleware"""
            BaseHTTPMiddleware.__init__(self, app)

        async def dispatch(self, request: Request, call_next: Callable) -> fastapi.Response:
            start_time = time.time()
            response = await call_next(request)
            end_time = time.time()
            diff = end_time - start_time
            size = response.headers.get("Content-Length", 0)
            logger.info(
                f"{request.method} {request.url.path}: "
                f"{response.status_code}: {int(size)/1024/1024:.3f} MB in {diff:.3f}s "
                f"({int(size) / 8 / 1024 / 1024 / diff:.3f} MB/s)"
            )
            return response

    def __init__(self, config: MapConfig, client: ApiClient):
        """
        Initialize the map interface

        Args:
            config: The configuration for the map
        """
        self._config = config
        self._client = client
        self._data = DataSource(client, config)
        self._session_secret = secrets.token_urlsafe(32)

        # Setup FastAPI app
        self._app = fastapi.FastAPI()
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "HEAD", "OPTIONS"],
            allow_headers=["*"],
        )
        self._app.add_middleware(
            MapInterface.SessionAuthenticator,
            paths={
                re.compile(r"^/aircrafts"): MapInterface.EmptyFeatureCollection(
                    headers={"X-Status-Code": "403"}
                ),
                re.compile(r"^/ui/static/icons/.*"): RedirectResponse(
                    url="/ui/static/icons/forbidden.png",
                    headers={"X-Status-Code": "403"}
                ),
            }
        )
        self._app.add_middleware(
            SessionMiddleware,
            secret_key=self._session_secret,
            session_cookie="flight_map_session",
            max_age=3600,
            same_site="lax",
            https_only=not self._config.app_dev_mode
        )
        self._app.add_middleware(MapInterface.RequestLoggerMiddleware)
        self._app.mount(
            "/ui/static",
            StaticFiles(directory=str(Path(__file__).parent / "static")),
            name="static"
        )
        self._app.add_api_route("/aircrafts", self.get_aircrafts_geojson, methods=["GET"])
        self._app.add_api_route("/ui/config", self.get_config, methods=["GET"])
        self._app.add_api_route("/health", self.health, methods=["GET"])
        self._app.add_api_route("/ui/bbox", self.update_bbox, methods=["POST"])
        add_applications({
            "/": self.create_map_widget,
            "/map": self.create_map_widget,  # legacy endpoint
        }, app=self._app, title="Local Flight Map")

        # Initialize map
        self._map = folium.Map(
            location=(self._config.map_center.latitude, self._config.map_center.longitude),
            zoom_start=self._config.map_zoom_start,
            max_bounds=self._config.map_max_bounds,
            control_scale=self._config.map_control_scale,
            max_lat=self._config.map_bbox.max_lat,
            min_lat=self._config.map_bbox.min_lat,
            max_lon=self._config.map_bbox.max_lon,
            min_lon=self._config.map_bbox.min_lon,
        )

        # Set map bounds
        self._map.fit_bounds(self._config.get_map_bounds())
        self._map.options["radius"] = self._config.map_radius

        # Initialize and add layers
        self._layers = MapLayers(self._map, self._config)
        self._layers.add_to_map()

        # Add static scripts to the document
        for script in Path(str(Path(__file__).parent / "static" / "js")).glob("*.js"):
            self._map.get_root().html.add_child(folium.Element(
                f'<script src="/ui/static/js/{script.name}"></script>'
            ))

        # Add inline map initialization script
        self._map.get_root().html.add_child(folium.Element(
            f'<script>{Path(__file__).with_suffix(".js").read_text()}</script>'
        ))

    async def __aenter__(self):
        """Enter the async context manager"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager"""
        if hasattr(self._client, '__aexit__'):
            await self._client.__aexit__(exc_type, exc_val, exc_tb)

    async def health(self) -> JSONResponse:
        """Health check endpoint"""
        return JSONResponse(
            content={"status": "ok"},
            status_code=200
        )

    async def get_config(self) -> JSONResponse:
        """
        Get the configuration

        Returns:
            JSONResponse: The configuration
        """
        return JSONResponse(
            content={
                "interval": self._config.map_refresh_interval,
                "bounds": {
                    "north": self._config.map_bbox.max_lat,
                    "south": self._config.map_bbox.min_lat,
                    "east": self._config.map_bbox.max_lon,
                    "west": self._config.map_bbox.min_lon
                },
                "center": {
                    "lat": self._config.map_center.latitude,
                    "lng": self._config.map_center.longitude
                },
                "radius": self._config.map_radius
            },
            status_code=200
        )

    async def get_aircrafts_geojson(self) -> JSONResponse:
        """
        API endpoint to get aircraft data

        Returns:
            JSONResponse: The aircraft data
        """
        try:

            aircrafts = await self._data.get_aircrafts_geojson()
            logger.info(f"Getting aircraft data for {self._config.map_bbox}: length {len(aircrafts['features'])}")
            if aircrafts is None:
                return MapInterface.EmptyFeatureCollection(headers={"X-Status-Code": "404"})
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
        """
        Create the map widget for Panel

        Returns:
            pn.pane.plot.Folium: The map widget
        """
        return pn.pane.plot.Folium(self._map, sizing_mode="stretch_both")

    async def update_bbox(self, request: Request) -> JSONResponse:
        """
        Update the bounding box

        Args:
            request: The request containing the new bounding box coordinates

        Returns:
            JSONResponse: The response indicating success or failure
        """
        try:
            data = await request.json()
            bounds = data.get("bounds", {})

            # Update map bounds
            self._map.options["max_lat"] = bounds.get("north")
            self._map.options["min_lat"] = bounds.get("south")
            self._map.options["max_lon"] = bounds.get("east")
            self._map.options["min_lon"] = bounds.get("west")

            # Create BBox and get center and radius
            bbox = BBox(
                min_lat=bounds.get("south"),
                max_lat=bounds.get("north"),
                min_lon=bounds.get("west"),
                max_lon=bounds.get("east")
            )
            center, radius = bbox.to_center_and_radius()

            # Update map configuration
            self._config.map_center = center
            self._config.map_radius = radius
            self._config.map_bbox = bbox  # Update the map_bbox property

            # Force a data refresh by triggering the boundsUpdated event
            self._map.get_root().html.add_child(folium.Element(
                '<script>\n'
                'window.dispatchEvent(new CustomEvent("boundsUpdated", {\n'
                '  detail: {\n'
                '    bounds: {\n'
                f'      north: {bounds.get("north")},\n'
                f'      south: {bounds.get("south")},\n'
                f'      east: {bounds.get("east")},\n'
                f'      west: {bounds.get("west")}\n'
                '    }\n'
                '  }\n'
                '}));\n'
                '</script>'
            ))

            return JSONResponse(
                content={"status": "ok"},
                status_code=200
            )
        except Exception as e:
            logger.error(f"Error updating bounding box: {e}")
            return JSONResponse(
                content={"error": str(e)},
                status_code=500
            )

    async def serve(self):
        """Start the server"""
        config = uvicorn.Config(
            self._app,
            host="0.0.0.0",
            port=self._config.app_port,
            log_level="error"
        )
        server = uvicorn.Server(config)
        shutdown_event = asyncio.Event()

        def handle_signal(sig: Union[signal.Signals, int], frame: FrameType):
            _ = frame
            logger.info(f"Received signal {signal.Signals(sig).name}, initiating graceful shutdown...")
            shutdown_event.set()

        signal.signal(signal.SIGTERM, handle_signal)
        signal.signal(signal.SIGINT, handle_signal)

        try:
            logger.info(f"Starting server on http://{config.host}:{config.port}")
            server_task = asyncio.create_task(server.serve())
            await shutdown_event.wait()

            logger.info("Shutting down server...")
            server.should_exit = True
            await server_task

        finally:
            logger.info("Cleaning up resources...")
            if hasattr(self._client, 'close'):
                await self._client.close()
            elif hasattr(self._client, '__aexit__'):
                await self._client.__aexit__(None, None, None)
            logger.info("Shutdown complete")
