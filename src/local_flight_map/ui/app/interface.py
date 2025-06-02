"""
Map interface module for the Local Flight Map application.
Provides the main interface for displaying and interacting with the flight map.
"""

import folium
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import (
    ORJSONResponse as JSONResponse,
    RedirectResponse,
    HTMLResponse,
    Response
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import secrets
from starlette.middleware.sessions import SessionMiddleware
import re
import signal
from types import FrameType
from typing import Union, Dict, Any

from ...api import ApiClients
from .config import MapConfig
from .layers import MapLayers
from .data import DataSource
from .config import BBox, logger
from .middleware import SessionAuthenticator, RequestLoggerMiddleware


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

    def __init__(
        self,
        config: MapConfig,
        clients: ApiClients
    ):
        """
        Initialize the map interface.

        Args:
            config: The configuration for the map.
            clients: The API clients for fetching aircraft data from ADSBExchange, HexDB, and OpenSky.
        """
        self._config = config
        self._clients = clients
        self._data = DataSource(clients, config)
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
        self._app = FastAPI()

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
            SessionAuthenticator,
            paths={
                re.compile(r"^/service/aircrafts"): MapInterface.EmptyFeatureCollection(
                    headers={"X-Status-Code": "403"}
                ),
                re.compile(r"^/ui/static/icons/(?!forbidden\.png).*"): RedirectResponse(
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
            same_site="lax" if self._config.app_dev_mode else "none",
            https_only=not self._config.app_dev_mode,
            path="/"
        )

        # Add request logger
        self._app.add_middleware(RequestLoggerMiddleware)

        # Mount static files
        self._app.mount(
            "/ui/static",
            StaticFiles(directory=str(Path(__file__).parent / "static")),
            name="static"
        )

        # Add routes
        self._app.add_api_route("/ui/config", self.get_config, methods=["GET"])
        self._app.add_api_route("/ui/config", self.update_config, methods=["POST"])
        self._app.add_api_route(
            "/auth/cookie-consent", self.handle_cookie_consent, methods=["GET", "POST"],
            response_model=None
        )
        self._app.add_api_route("/auth/status", self.check_auth_status, methods=["GET"])
        self._app.add_api_route("/service/health", self.health, methods=["GET"])
        self._app.add_api_route("/service/aircrafts", self.get_aircrafts_geojson, methods=["GET"])

        # Add main map route
        self._app.add_api_route("/", self.get_map, methods=["GET"])
        self._app.add_api_route("/map", self.get_map, methods=["GET"])

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

    def _apply_cookie_consent(self, response: Response) -> Response:
        """
        Apply cookie consent to the response.
        """
        response.set_cookie(
            "cookie_consent",
            "true",
            max_age=60 * 60 * 24 * 365,  # 1 year
            httponly=True,
            samesite="lax" if self._config.app_dev_mode else "none",
            secure=not self._config.app_dev_mode,
            path="/"
        )
        return response

    def _add_static_scripts(self):
        """
        Add static JavaScript files to the map.
        Includes both external scripts and inline initialization code.
        """
        # Add custom CSS
        css = """
        <link rel="stylesheet" href="/ui/static/css/main.css">
        """
        root = self._map.get_root()
        root.header.add_child(folium.Element(css))

        # Add static scripts
        static_scripts = list((Path(__file__).parent / "static" / "js").glob("*.js"))
        static_scripts.sort()
        if len(static_scripts) == 0:
            raise FileNotFoundError("No static scripts found")

        for script in static_scripts:
            root.html.add_child(folium.Element(
                    f'<script src="/ui/static/js/{script.name}"></script>'
            ))

        # Add inline map initialization script
        root.html.add_child(folium.Element(
            f'<script>{Path(__file__).with_suffix(".js").read_text()}</script>'
        ))

    async def get_map(self, request: Request) -> HTMLResponse:
        """
        Get the map HTML page.

        Args:
            request: The HTTP request.

        Returns:
            HTMLResponse: The map HTML page.
        """
        return HTMLResponse(
            content=self._map.get_root().render(),
            status_code=200
        )

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
        for client in self._clients:
            await client.__aexit__(exc_type, exc_val, exc_tb)

    async def check_auth_status(self, request: Request) -> JSONResponse:
        """
        Check the authentication status of the current session.

        Args:
            request: The HTTP request.

        Returns:
            JSONResponse: The authentication status.
        """
        return JSONResponse(
            content={
                "authenticated": request.session.get("authenticated", False),
                "cookie_consent": request.session.get("cookie_consent", False)
            },
            status_code=200
        )

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
                "radius": self._config.map_radius,
                "data_provider": self._config.data_provider
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
            if data is None:
                logger.warning("No aircraft data returned from data source")
                return MapInterface.EmptyFeatureCollection()
            return JSONResponse(
                content=data,
                status_code=200
            )
        except Exception as e:
            logger.error(f"Error getting aircraft data: {e}", exc_info=True)
            return MapInterface.EmptyFeatureCollection(
                headers={"X-Status-Code": "500"}
            )

    async def handle_cookie_consent(self, request: Request) -> Union[JSONResponse, RedirectResponse]:
        """
        Handle cookie consent from the client.
        Supports both GET (with query parameters) and POST (with JSON body) requests.
        Sets a consent cookie and updates the session.

        Args:
            request: The HTTP request containing consent information.

        Returns:
            Union[JSONResponse, RedirectResponse]: A response indicating success or failure.
            For GET requests, redirects to the main page. For POST requests, returns JSON.
        """
        try:
            # Handle GET request with query parameters
            if request.method == "GET":
                consent = request.query_params.get("consent", "").lower() == "true"
                if consent:
                    request.session.update(dict.fromkeys(["cookie_consent", "authenticated"], True))
                    return self._apply_cookie_consent(RedirectResponse(url="/", status_code=303))

                return RedirectResponse(url="/", status_code=303)

            # Handle POST request with JSON body
            data = await request.json()
            if data.get("consent") is True:
                request.session.update(dict.fromkeys(["cookie_consent", "authenticated"], True))
                return self._apply_cookie_consent(JSONResponse(
                    content={"status": "ok"},
                    status_code=200
                ))

            return JSONResponse(
                content={"status": "error", "message": "Consent not given"},
                status_code=400
            )
        except Exception as e:
            logger.error(f"Error handling cookie consent: {e}")
            if request.method == "GET":
                return RedirectResponse(url="/", status_code=303)
            return JSONResponse(
                content={"status": "error", "message": str(e)},
                status_code=500
            )

    async def update_config(self, request: Request) -> JSONResponse:
        """
        Update the map's bounding box.

        Args:
            request: The HTTP request containing the new bounding box coordinates.

        Returns:
            JSONResponse: A response indicating success or failure.
        """
        try:
            data = await request.json()
            bounds_data = data.get("bounds", data)
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
        logger.info(f"Starting server on  {config.host}:{config.port}")
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
