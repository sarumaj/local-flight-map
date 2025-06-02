from typing import Optional, Union, Tuple, Callable
from async_lru import alru_cache
from datetime import datetime
from collections import defaultdict
import asyncio

from ..base import BaseClient, BBox, OAuth2AuthMiddleware
from .config import OpenSkyConfig
from .response import States, FlightTrack


class OpenSkyClient(BaseClient):
    """
    Client for interacting with the OpenSky Network API.

    This class provides methods for fetching aircraft states, tracks, and other
    flight data from the OpenSky Network API. It includes caching to improve
    performance and reduce API calls.

    The client supports:
    - Fetching all aircraft states
    - Fetching states from own sensors (requires authentication)
    - Fetching flight tracks
    - Rate limiting for API requests
    """

    def __init__(self, config: Optional[OpenSkyConfig] = None):
        """
        Initialize a new OpenSky Network API client.

        Args:
            config: Optional configuration for the client. If not provided,
                   default configuration will be used.
        """
        config = config or OpenSkyConfig()
        BaseClient.__init__(
            self,
            config=config,
            base_url=config.opensky_base_url,
            middlewares=(
                OAuth2AuthMiddleware(
                    auth_url=config.opensky_auth_url,
                    client_id=config.opensky_client_id,
                    client_secret=config.opensky_client_secret,
                    grant_type="client_credentials"
                ),
            )
        )
        self._last_requests = defaultdict(lambda: 0)
        self._rate_limit_lock = asyncio.Lock()
        self._access_token = None
        self._token_expiry = 0

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Clean up resources when exiting the async context.

        This method ensures that all cached data is properly cleared and
        connections are closed.

        Args:
            exc_type: The type of exception that was raised, if any.
            exc_val: The exception value that was raised, if any.
            exc_tb: The traceback of the exception, if any.
        """
        await self.get_states_from_opensky.cache_close()
        await self.get_my_states_from_opensky.cache_close()
        await self.get_track_by_aircraft_from_opensky.cache_close()
        await super(OpenSkyClient, self).__aexit__(exc_type, exc_val, exc_tb)

    async def _apply_opensky_rate_limit(self, method: Callable):
        """
        Apply rate limiting to OpenSky API requests.

        This method ensures that requests to the OpenSky API are rate-limited
        according to the configured window.

        Args:
            method: The async method to rate limit.

        Returns:
            The result of the rate-limited method.
        """
        now = int(datetime.now().timestamp())
        window = (
            self._config.opensky_rate_limit_window_auth
            if self._config.opensky_client_id and self._config.opensky_client_secret
            else self._config.opensky_rate_limit_window_no_auth
        )
        await self._rate_limit_lock.acquire()
        if now - self._last_requests[method] < window:
            await asyncio.sleep(window - (now - self._last_requests[method]))
        self._last_requests[method] = now
        self._rate_limit_lock.release()

    @alru_cache(ttl=0.1)
    async def get_states_from_opensky(
        self,
        time_secs: Union[int, datetime] = 0,
        icao24: Optional[Union[str, Tuple[str, ...]]] = None,
        bbox: Optional[BBox] = None
    ) -> Optional[States]:
        """
        Get all aircraft states from OpenSky Network.

        This method fetches the current state vectors of all aircraft from the
        OpenSky Network API. The response is cached to improve performance.

        Args:
            time_secs: The time for which to fetch states (Unix timestamp or datetime).
            icao24: Optional ICAO24 address(es) to filter by.
            bbox: Optional bounding box to filter by.

        Returns:
            Optional[States]: The aircraft states if found, None otherwise.

        Raises:
            ValueError: If the bounding box is invalid.
        """
        if bbox:
            bbox.validate()

        params = {'extended': 1}
        if time_secs:
            if isinstance(time_secs, datetime):
                time_secs = int(time_secs.timestamp())
            params['time'] = time_secs

        if icao24:
            if isinstance(icao24, (tuple, list)):
                params['icao24'] = ','.join(map(lambda x: str(x).strip().lower(), icao24))
            else:
                params['icao24'] = icao24

        if bbox:
            bbox.validate()
            params.update({
                'lamin': bbox.min_lat,
                'lamax': bbox.max_lat,
                'lomin': bbox.min_lon,
                'lomax': bbox.max_lon
            })
        await self._apply_opensky_rate_limit(self.get_states_from_opensky)
        async with self._session.get(
            "/api/states/all",
            params=params
        ) as response:
            data = await self._handle_response(response)
            return States.from_dict(data) if data else None

    @alru_cache(ttl=0.1)
    async def get_my_states_from_opensky(
        self,
        time_secs: Union[int, datetime] = 0,
        icao24: Optional[Union[str, Tuple[str, ...]]] = None,
        serials: Optional[Union[int, Tuple[int, ...]]] = None
    ) -> Optional[States]:
        """
        Get states from own sensors from OpenSky Network.

        This method fetches the current state vectors of aircraft from the user's
        own sensors. Authentication is required for this operation.

        Args:
            time_secs: The time for which to fetch states (Unix timestamp or datetime).
            icao24: Optional ICAO24 address(es) to filter by.
            serials: Optional sensor serial number(s) to filter by.

        Returns:
            Optional[States]: The aircraft states if found, None otherwise.

        Raises:
            ValueError: If authentication is not configured.
        """
        if not self._config.opensky_client_id or not self._config.opensky_client_secret:
            raise ValueError("OAuth2 client credentials required for this operation")

        params = {'extended': 1}
        if time_secs:
            if isinstance(time_secs, datetime):
                params['time'] = int(time_secs.timestamp())
            else:
                params['time'] = time_secs

        if icao24:
            if isinstance(icao24, (tuple, list)):
                params['icao24'] = ','.join(map(lambda x: str(x).strip().lower(), icao24))
            else:
                params['icao24'] = icao24

        if serials:
            if isinstance(serials, (tuple, list)):
                params['serials'] = ','.join(map(lambda x: str(x).strip(), serials))
            else:
                params['serials'] = serials

        await self._apply_opensky_rate_limit(self.get_my_states_from_opensky)
        async with self._session.get(
            "/api/states/own",
            params=params
        ) as response:
            data = await self._handle_response(response)
            return States.from_dict(data) if data else None

    @alru_cache(ttl=0.1)
    async def get_track_by_aircraft_from_opensky(
        self,
        icao24: str,
        time_secs: Union[int, datetime] = 0
    ) -> Optional[FlightTrack]:
        """
        Get flight track by aircraft from OpenSky Network.

        This method fetches the complete flight track of an aircraft from the
        OpenSky Network API. The response is cached to improve performance.

        Args:
            icao24: The ICAO24 address of the aircraft.
            time_secs: The time for which to fetch the track (Unix timestamp or datetime).

        Returns:
            Optional[FlightTrack]: The flight track if found, None otherwise.

        Raises:
            ValueError: If the time is too old (more than 30 days ago).
        """
        params = {'icao24': icao24}
        if isinstance(time_secs, datetime):
            params['time'] = int(time_secs.timestamp())
        else:
            params['time'] = time_secs

        if int(datetime.now().timestamp()) - params['time'] > 2592 * 1e3 and params['time'] != 0:
            raise ValueError("It is not possible to access flight tracks from more than 30 days in the past.")

        await self._apply_opensky_rate_limit(self.get_track_by_aircraft_from_opensky)
        async with self._session.get(
            "/api/tracks/all",
            params=params
        ) as response:
            data = await self._handle_response(response)
            return FlightTrack.from_dict(data) if data else None
