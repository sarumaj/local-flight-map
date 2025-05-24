import folium
import panel as pn
import uvicorn
from panel.io.fastapi import add_applications
import fastapi
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
import secrets
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from typing import Callable
import time

from ...api import ApiClient
from .config import MapConfig
from .layers import MapLayers
from .data import DataSource


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("local-flight-map")


class MapInterface:
    """Main interface for the flight map application"""

    class EmptyFeatureCollection(JSONResponse):
        """Empty feature collection"""
        def __init__(self):
            JSONResponse.__init__(
                self,
                content={
                    "type": "FeatureCollection",
                    "features": []
                },
                status_code=200
            )

    class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
        """Middleware to redirect HTTP requests to HTTPS"""
        def __init__(self, app: fastapi.FastAPI, dev_mode: bool = False):
            BaseHTTPMiddleware.__init__(self, app)
            self._dev_mode = dev_mode

        async def dispatch(self, request: Request, call_next) -> fastapi.Response:
            if not self._dev_mode and request.url.scheme == "http":
                url = request.url.replace(scheme="https")
                return RedirectResponse(url=url)
            return await call_next(request)

    class SessionAuthenticator(BaseHTTPMiddleware):
        """Session authenticator"""
        def __init__(self, app: fastapi.FastAPI, dev_mode: bool = False):
            """
            Initialize the session authenticator

            Args:
                app: The FastAPI app
                dev_mode: Whether to run in development mode
            """
            BaseHTTPMiddleware.__init__(self, app)
            self._dev_mode = dev_mode

        async def dispatch(self, request: Request, call_next: Callable) -> fastapi.Response:
            if "authenticated" not in request.session:
                request.session["authenticated"] = True
                return MapInterface.EmptyFeatureCollection()
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
        self._data = DataSource(client)
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
        self._app.add_middleware(MapInterface.SessionAuthenticator, dev_mode=self._config.dev_mode)
        self._app.add_middleware(
            SessionMiddleware,
            secret_key=self._session_secret,
            session_cookie="flight_map_session",
            max_age=3600,
            same_site="lax",
            https_only=not self._config.dev_mode
        )
        self._app.add_middleware(MapInterface.HTTPSRedirectMiddleware, dev_mode=self._config.dev_mode)
        self._app.add_middleware(MapInterface.RequestLoggerMiddleware)
        self._app.mount(
            "/ui/static",
            StaticFiles(directory=str(Path(__file__).parent / "static")),
            name="static"
        )
        self._app.add_api_route("/aircrafts", self.get_aircrafts_geojson, methods=["GET"])
        add_applications({"/": self.create_map_widget}, app=self._app, title="Local Flight Map")

        # Initialize map
        self._map = folium.Map(
            location=(self._config.center.latitude, self._config.center.longitude),
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
        self._map.options["radius"] = self._config.radius

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
        """
        API endpoint to get aircraft data

        Returns:
            JSONResponse: The aircraft data
        """
        try:
            aircrafts = await self._data.get_aircrafts_geojson(self._config)
            if aircrafts is None:
                return MapInterface.EmptyFeatureCollection()
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

    async def serve(self):
        """Start the server"""
        config = uvicorn.Config(
            self._app,
            host="localhost",
            port=self._config.port,
            log_level="error"
        )
        server = uvicorn.Server(config)
        try:
            await server.serve()
        finally:
            if hasattr(self._client, 'close'):
                await self._client.close()
            elif hasattr(self._client, '__aexit__'):
                await self._client.__aexit__(None, None, None)
