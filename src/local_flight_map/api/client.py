import aiohttp
from typing import Optional, List, Union, Callable, Any
from datetime import datetime
from collections import defaultdict
import asyncio
from async_lru import alru_cache

from .request_params import StatesRequestParams, MyStatesRequestParams, TrackRequestParams, BBox
from .response_objects import States, FlightTrack
from .response_objects import RouteInformation, AirportInformation, AircraftInformation
from .config import ApiConfig


class ApiClient:
    def __init__(self, config: Optional[ApiConfig] = None):
        self._config = config or ApiConfig()
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_requests = defaultdict(lambda: 0)
        self._rate_limit_lock = asyncio.Lock()

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(
            auth=aiohttp.BasicAuth(
                self._config.opensky_username,
                self._config.opensky_password
            ) if self._config.opensky_username else None
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        _ = (exc_type, exc_val, exc_tb)
        if self._session:
            await self._session.close()
            self._session = None
        await self.get_aircraft_information.cache_close()
        await self.get_airport_information.cache_close()
        await self.get_route_information.cache_close()

    async def _apply_rate_limit(self, method: Callable):
        now = int(datetime.now().timestamp())
        window = (
            self._config.opensky_rate_limit_window_auth
            if self._config.opensky_username
            else self._config.opensky_rate_limit_window_no_auth
        )
        await self._rate_limit_lock.acquire()
        if now - self._last_requests[method] < window:
            await asyncio.sleep(window - (now - self._last_requests[method]))
        self._last_requests[method] = now
        self._rate_limit_lock.release()

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Optional[Any]:
        if response.status == 404:
            return None

        response.raise_for_status()
        return await response.json() or None

    async def get_states(
        self,
        time_secs: Union[int, datetime] = 0,
        icao24: Optional[Union[str, List[str]]] = None,
        bbox: Optional[BBox] = None
    ) -> Optional[States]:
        """Retrieve state vectors for a given time."""
        params: StatesRequestParams = {}

        if time_secs:
            if isinstance(time_secs, datetime):
                time_secs = int(time_secs.timestamp())
            params['time'] = time_secs

        if icao24:
            if isinstance(icao24, list):
                icao24 = ','.join(map(lambda x: str(x).strip().lower(), icao24))
            params['icao24'] = icao24

        if bbox:
            for value in bbox:
                if 180 < value < -180:
                    raise ValueError(f"Invalid bounding box value: {value}")
            params['lamax'] = bbox.max_lon
            params['lomax'] = bbox.max_lat
            params['lomin'] = bbox.min_lon
            params['lamin'] = bbox.min_lat

        await self._apply_rate_limit(self.get_states)
        async with self._session.get(f"{self._config.opensky_base_url}/states/all", params=params) as response:
            data = await self._handle_response(response)
            return States.from_dict(data) if data else None

    async def get_my_states(
        self,
        time_secs: Union[int, datetime] = 0,
        icao24: Optional[Union[str, List[str]]] = None,
        serials: Optional[Union[int, List[int]]] = None
    ) -> Optional[States]:
        """Retrieve state vectors for your own sensors."""
        if not self._config.opensky_username or not self._config.opensky_password:
            raise ValueError("Authentication required for this operation")

        params: MyStatesRequestParams = {'extended': 1}

        if time_secs:
            if isinstance(time_secs, datetime):
                time_secs = int(time_secs.timestamp())
            params['time'] = time_secs

        if icao24:
            if isinstance(icao24, list):
                icao24 = ','.join(map(lambda x: str(x).strip().lower(), icao24))
            params['icao24'] = icao24

        if serials:
            if isinstance(serials, list):
                serials = ','.join(map(lambda x: str(x).strip(), serials))
            params['serials'] = serials

        await self._apply_rate_limit(self.get_my_states)
        async with self._session.get(f"{self._config.opensky_base_url}/states/own", params=params) as response:
            data = await self._handle_response(response)
            return States.from_dict(data) if data is not None else None

    @alru_cache(maxsize=1000)
    async def get_track_by_aircraft(
        self,
        icao24: str,
        time: Union[int, datetime] = 0
    ) -> Optional[FlightTrack]:
        """Retrieve the trajectory for a specific aircraft."""
        if isinstance(time, datetime):
            time = int(time.timestamp())

        if int(datetime.now().timestamp()) - time > 2592 * 1e3 and time != 0:
            raise ValueError("It is not possible to access flight tracks from more than 30 days in the past.")

        params: TrackRequestParams = {
            'icao24': icao24.strip().lower(),
            'time': time
        }

        await self._apply_rate_limit(self.get_track_by_aircraft)
        async with self._session.get(f"{self._config.opensky_base_url}/tracks/all", params=params) as response:
            data = await self._handle_response(response)
            return FlightTrack.from_dict(data) if data else None

    @alru_cache(maxsize=1000)
    async def get_route_information(
        self,
        callsign: str,
    ) -> Optional[RouteInformation]:
        async with self._session.get(
            f"{self._config.hexdb_base_url}/route/icao/{callsign.lower().strip()}"
        ) as response:
            data = await self._handle_response(response)
            return RouteInformation.from_dict(data) if data else None

    @alru_cache(maxsize=1000)
    async def get_airport_information(
        self,
        icao24: str
    ) -> Optional[AirportInformation]:
        async with self._session.get(
            f"{self._config.hexdb_base_url}/airport/icao/{icao24.lower().strip()}"
        ) as response:
            data = await self._handle_response(response)
            return AirportInformation.from_dict(data) if data else None

    @alru_cache(maxsize=1000)
    async def get_aircraft_information(
        self,
        icao24: str
    ) -> Optional[AircraftInformation]:
        async with self._session.get(
            f"{self._config.hexdb_base_url}/aircraft/icao/{icao24.lower().strip()}"
        ) as response:
            data = await self._handle_response(response)
            return AircraftInformation.from_dict(data) if data else None
