import aiohttp
from typing import Optional, List, Tuple, Union
from datetime import datetime

from .request_params import StatesRequestParams, MyStatesRequestParams, TrackRequestParams
from .response_objects import StateVector, OpenSkyStates, FlightTrack, Waypoint
from .config import OpenSkyConfig


class OpenSkyApi:
    def __init__(self, config: Optional[OpenSkyConfig] = None):
        self._config = config or OpenSkyConfig()
        self._session: Optional[aiohttp.ClientSession] = None

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

    async def get_states(
        self,
        time_secs: Union[int, datetime] = 0,
        icao24: Optional[Union[str, List[str]]] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None
    ) -> Optional[OpenSkyStates]:
        """Retrieve state vectors for a given time."""
        params: StatesRequestParams = {}
        
        if time_secs:
            if isinstance(time_secs, datetime):
                time_secs = int(time_secs.timestamp())
            params['time'] = time_secs
        
        if icao24:
            if isinstance(icao24, list):
                icao24 = ','.join(icao24)
            params['icao24'] = icao24
            
        if bbox:
            for value in bbox:
                if 180 < value < -180:
                    raise ValueError(f"Invalid bounding box value: {value}")
            params['lamin'], params['lamax'], params['lomin'], params['lomax'] = bbox

        async with self._session.get(f"{self._config.opensky_base_url}/states/all", params=params) as response:
            response.raise_for_status()
            
            data = await response.json()
            if not data or 'states' not in data:
                raise Exception(f"Failed to get states: {data}")

            states = [
                StateVector.from_list(state)
                for state in data['states']
                if state
            ]

            return OpenSkyStates(time=data['time'], states=states)

    async def get_my_states(
        self,
        time_secs: Union[int, datetime] = 0,
        icao24: Optional[Union[str, List[str]]] = None,
        serials: Optional[Union[int, List[int]]] = None
    ) -> Optional[OpenSkyStates]:
        """Retrieve state vectors for your own sensors."""
        if not self._config.opensky_username or not self._config.opensky_password:
            raise ValueError("Authentication required for this operation")

        params: MyStatesRequestParams = {}
        
        if time_secs:
            if isinstance(time_secs, datetime):
                time_secs = int(time_secs.timestamp())
            params['time'] = time_secs

        if icao24:
            if isinstance(icao24, list):
                icao24 = ','.join(icao24)
            params['icao24'] = icao24

        if serials:
            if isinstance(serials, list):
                serials = ','.join(map(str, serials))
            params['serials'] = serials

        async with self._session.get(f"{self._config.opensky_base_url}/states/own", params=params) as response:
            response.raise_for_status()

            data = await response.json()
            if not data or 'states' not in data:
                raise Exception(f"Failed to get states: {data}")

            states = [
                StateVector.from_list(state)
                for state in data['states']
                if state
            ]

            return OpenSkyStates(time=data['time'], states=states)

    async def get_track_by_aircraft(
        self,
        icao24: str,
        time: Union[int, datetime] = 0
    ) -> Optional[FlightTrack]:
        """Retrieve the trajectory for a specific aircraft."""
        if isinstance(time, datetime):
            time = int(time.timestamp())

        params: TrackRequestParams = {
            'icao24': icao24.lower(),
            'time': time
        }

        async with self._session.get(f"{self._config.opensky_base_url}/tracks/all", params=params) as response:
            response.raise_for_status()

            data = await response.json()
            if not data:
                raise Exception("Failed to get track: No data returned")

            path = [
                Waypoint.from_list(point)
                for point in data['path']
                if point
            ]

            return FlightTrack(
                icao24=data['icao24'],
                start_time=data['startTime'],
                end_time=data['endTime'],
                callsign=data.get('callsign'),
                path=path
            )