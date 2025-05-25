"""
Map interface module for the Local Flight Map application.
Provides the main interface for displaying and interacting with the flight map.
"""

import folium
import panel as pn
import uvicorn
from panel.io.fastapi import add_applications
import fastapi
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import secrets
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from typing import Callable, Union, Dict, Any
import re
import time
import signal
from types import FrameType

from ...api import ApiClient
from .config import MapConfig
from .layers import MapLayers
from .data import DataSource
from .config import BBox, logger


class MapInterface:
    """
    Main interface for the flight map application.
    Handles map initialization, API endpoints, and user interactions.
    """

    class EmptyFeatureCollection(JSONResponse):
        """
        Empty feature collection response.
        Used when no aircraft data is available or when access is denied.
        """
        def __init__(self, **kwargs: Dict[str, Any]):
            """
            Initialize an empty feature collection response.

            Args:
                **kwargs: Additional keyword arguments to pass to JSONResponse.
            """
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
        """
        Session authenticator middleware.
        Handles authentication for protected routes.
        """
        def __init__(self, app: fastapi.FastAPI, paths: Dict[re.Pattern, Response] = None):
            """
            Initialize the session authenticator.

            Args:
                app: The FastAPI app to add middleware to.
                paths: Dictionary mapping regex patterns to responses for path-based authentication.
            """
            BaseHTTPMiddleware.__init__(self, app)
            self._paths = paths

        async def dispatch(self, request: Request, call_next: Callable) -> fastapi.Response:
            """
            Process the request and handle authentication.

            Args:
                request: The incoming request.
                call_next: The next middleware in the chain.

            Returns:
                The response from the next middleware or an authentication response.
            """
            if self._paths is not None:
                for path, response in self._paths.items():
                    if path.match(request.url.path):
                        if "authenticated" not in request.session:
                            request.session["authenticated"] = True
                            return response
            return await call_next(request)

    class RequestLoggerMiddleware(BaseHTTPMiddleware):
        """
        Request logger middleware.
        Logs information about each request including timing and response size.
        """
        def __init__(self, app: fastapi.FastAPI):
            """
            Initialize the request logger middleware.

            Args:
                app: The FastAPI app to add middleware to.
            """
            BaseHTTPMiddleware.__init__(self, app)

        async def dispatch(self, request: Request, call_next: Callable) -> fastapi.Response:
            """
            Process the request and log information about it.

            Args:
                request: The incoming request.
                call_next: The next middleware in the chain.

            Returns:
                The response from the next middleware.
            """
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
        Initialize the map interface.

        Args:
            config: The configuration for the map.
            client: The API client for fetching aircraft data.
        """
        self._config = config
        self._client = client
        self._data = DataSource(client, config)
        self._session_secret = secrets.token_urlsafe(32)
        self._map = None
        self._layers = None

        self._setup_fastapi()
        self._initialize_map()

    def _setup_fastapi(self):
        """
        Setup FastAPI application and middleware.
        Configures CORS, session handling, authentication, and routes.
        """
        self._app = fastapi.FastAPI()

        # Add CORS middleware
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "HEAD", "OPTIONS"],
            allow_headers=["*"],
        )

        # Add session authenticator
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

        # Add session middleware
        self._app.add_middleware(
            SessionMiddleware,
            secret_key=self._session_secret,
            session_cookie="flight_map_session",
            max_age=3600,
            same_site="lax",
            https_only=not self._config.app_dev_mode
        )

        # Add request logger
        self._app.add_middleware(MapInterface.RequestLoggerMiddleware)

        # Mount static files
        self._app.mount(
            "/ui/static",
            StaticFiles(directory=str(Path(__file__).parent / "static")),
            name="static"
        )

        # Add routes
        self._app.add_api_route("/aircrafts", self.get_aircrafts_geojson, methods=["GET"])
        self._app.add_api_route("/ui/config", self.get_config, methods=["GET"])
        self._app.add_api_route("/health", self.health, methods=["GET"])
        self._app.add_api_route("/ui/bbox", self.update_bbox, methods=["POST"])

        # Add Panel applications
        add_applications({
            "/": self.create_map_widget,
            "/map": self.create_map_widget,  # legacy endpoint
        }, app=self._app, title="Local Flight Map")

    def _initialize_map(self):
        """
        Initialize the map with configuration.
        Sets up the map view, bounds, and layers.
        """
        # Add Leaflet library to the head section before creating the map
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

        self._map.fit_bounds(self._config.get_map_bounds())
        self._map.options["radius"] = self._config.map_radius

        self._layers = MapLayers(self._map, self._config)
        self._layers.add_to_map()

        self._add_static_scripts()

    def _add_static_scripts(self):
        """
        Add static JavaScript files to the map.
        Includes both external scripts and inline initialization code.
        """
        # Add static scripts
        for script in Path(str(Path(__file__).parent / "static" / "js")).glob("*.js"):
            self._map.get_root().html.add_child(folium.Element(
                f'<script defer src="/ui/static/js/{script.name}"></script>'
            ))

        # Add inline map initialization script
        self._map.get_root().html.add_child(folium.Element(
            f'<script defer>{Path(__file__).with_suffix(".js").read_text()}</script>'
        ))

    async def __aenter__(self):
        """
        Enter the async context manager.

        Returns:
            self: The initialized map interface instance.
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the async context manager.
        Cleans up resources and closes connections.

        Args:
            exc_type: The type of exception that was raised, if any.
            exc_val: The exception value that was raised, if any.
            exc_tb: The traceback of the exception, if any.
        """
        if hasattr(self._client, '__aexit__'):
            await self._client.__aexit__(exc_type, exc_val, exc_tb)

    async def health(self) -> JSONResponse:
        """
        Health check endpoint.

        Returns:
            JSONResponse: A response indicating the service is healthy.
        """
        return JSONResponse(
            content={"status": "ok"},
            status_code=200
        )

    async def get_config(self) -> JSONResponse:
        """
        Get the current map configuration.

        Returns:
            JSONResponse: The map configuration including bounds, center, and refresh interval.
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
        API endpoint to get aircraft data in GeoJSON format.

        Returns:
            JSONResponse: The aircraft data as a GeoJSON feature collection.
        """
        try:
            data = await self._data.get_aircrafts_geojson()
            return JSONResponse(
                content=data,
                status_code=200
            )
        except Exception as e:
            logger.error(f"Error getting aircraft data: {e}")
            return MapInterface.EmptyFeatureCollection(
                headers={"X-Status-Code": "500"}
            )

    def create_map_widget(self):
        """
        Create the map widget for the Panel interface.

        Returns:
            The Panel widget containing the map.
        """
        return pn.pane.plot.Folium(
            self._map,
            sizing_mode="stretch_both"
        )

    async def update_bbox(self, request: Request) -> JSONResponse:
        """
        Update the map's bounding box.

        Args:
            request: The HTTP request containing the new bounding box coordinates.

        Returns:
            JSONResponse: A response indicating success or failure.
        """
        try:
            data = await request.json()
            logger.info(f"Received bbox update request data: {data}")
            bounds_data = data.get("bounds", data)  # Handle both nested and flat structures
            self._config.map_bbox = BBox(
                min_lat=bounds_data["south"],
                max_lat=bounds_data["north"],
                min_lon=bounds_data["west"],
                max_lon=bounds_data["east"]
            )
            return JSONResponse(
                content={"status": "ok"},
                status_code=200
            )
        except Exception as e:
            logger.error(f"Error updating bounding box: {e}")
            return JSONResponse(
                content={"status": "error", "message": str(e)},
                status_code=400
            )

    async def serve(self):
        """
        Start the web server and serve the map interface.
        Handles graceful shutdown on SIGINT and SIGTERM.
        """
        config = uvicorn.Config(
            self._app,
            host="0.0.0.0",
            port=self._config.app_port,
            log_level="error"
        )
        server = uvicorn.Server(config)

        def handle_signal(sig: Union[signal.Signals, int], frame: FrameType):
            """
            Handle shutdown signals.

            Args:
                sig: The signal that was received.
                frame: The current stack frame.
            """
            logger.info(f"Received signal {sig}, shutting down...")
            server.should_exit = True

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        await server.serve()
