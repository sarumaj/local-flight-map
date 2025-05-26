"""
OpenSky API module for the Local Flight Map application.
Provides classes and utilities for interacting with the OpenSky Network API to fetch aircraft states,
tracks, and other flight data.
"""

from typing import Optional, List, Union, Callable, Any, Dict, Tuple
from datetime import datetime
import asyncio
from async_lru import alru_cache
from dataclasses import dataclass
from pydantic import Field
import aiohttp
from collections import defaultdict

from .base import BaseClient, BaseConfig, BBox, ResponseObject


@dataclass
class StateVector(ResponseObject):
    """
    Represents a state vector of an aircraft from the OpenSky Network.

    This class stores the current state of an aircraft, including its position,
    altitude, velocity, and other flight-related information.

    Attributes:
        icao24: The ICAO24 address of the transmitter in hex string representation.
        callsign: The callsign of the vehicle. Can be None if no callsign has been received.
        origin_country: The country inferred through the ICAO24 address.
        time_position: The seconds since epoch of last position report.
                      Can be None if there was no position report received by OpenSky within 15s
                      before the current time.
        last_contact: The last time the aircraft was in contact with the system.
        longitude: The longitude of the aircraft. Can be None.
        latitude: The latitude of the aircraft. Can be None.
        baro_altitude: The barometric altitude of the aircraft. Can be None.
        on_ground: Whether the aircraft is on the ground (the vehicle sends ADS-B surface position reports).
        velocity: The velocity of the aircraft over ground in m/s. Can be None.
        true_track: The true track of the aircraft in decimal degrees (0 is north). Can be None.
        vertical_rate: The vertical rate of the aircraft in m/s, incline is positive, decline negative.
                      Can be None.
        sensors: The serial numbers of sensors which received messages from the vehicle within the validity
                period of this state vector. Can be None if no filtering for sensor has been requested.
        geo_altitude: The geometric altitude of the aircraft in meters. Can be None.
        squawk: The squawk code of the aircraft. Can be None.
        spi: Whether the aircraft is in special position indication mode.
        position_source: The source of the position data:
                        0 = ADS-B,
                        1 = ASTERIX,
                        2 = MLAT,
                        3 = FLARM.
        category: The category of the aircraft:
                    0 = No information at all,
                    1 = No ADS-B Emitter Category Information,
                    2 = Light (< 15500 lbs),
                    3 = Small (15500 to 75000 lbs),
                    4 = Large (75000 to 300000 lbs),
                    5 = High Vortex Large (aircraft such as B-757),
                    6 = Heavy (> 300000 lbs),
                    7 = High Performance (> 5g acceleration and 400 kts),
                    8 = Rotorcraft,
                    9 = Glider / sailplane,
                    10 = Lighter-than-air,
                    11 = Parachutist / Skydiver,
                    12 = Ultralight / hang-glider / paraglider,
                    13 = Reserved,
                    14 = Unmanned Aerial Vehicle,
                    15 = Space / Trans-atmospheric vehicle,
                    16 = Surface Vehicle – Emergency Vehicle,
                    17 = Surface Vehicle – Service Vehicle,
                    18 = Point Obstacle (includes tethered balloons),
                    19 = Cluster Obstacle,
                    20 = Line Obstacle.
    """
    icao24: str
    callsign: Optional[str]
    origin_country: str
    time_position: Optional[int]
    last_contact: int
    longitude: Optional[float]
    latitude: Optional[float]
    baro_altitude: Optional[float]
    on_ground: bool
    velocity: Optional[float]
    true_track: Optional[float]
    vertical_rate: Optional[float]
    sensors: Optional[List[int]]
    geo_altitude: Optional[float]
    squawk: Optional[str]
    spi: bool
    position_source: int
    category: Optional[int]

    def to_geojson(self) -> Dict[str, Any]:
        """
        Convert the state vector to GeoJSON format.

        This method creates a GeoJSON feature representing the aircraft's current
        position and state.

        Returns:
            A GeoJSON feature containing the aircraft's position and state properties.
        """
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude]
            },
            "properties": {
                "icao24_code": self.icao24,
                "callsign": self.callsign,
                "origin_country": self.origin_country,
                "time_position": self.time_position,
                "last_contact": self.last_contact,
                "longitude": self.longitude,
                "latitude": self.latitude,
                "baro_altitude": self.baro_altitude,
                "on_ground": self.on_ground,
                "velocity": self.velocity,
                "track_angle": self.true_track,
                "vertical_rate": self.vertical_rate,
                "sensors": self.sensors,
                "geo_altitude": self.geo_altitude,
                "squawk_code": self.squawk,
                "special_position_indicator_flag": self.spi,
                "position_source": self.position_source,
                "category": self.category,
            }
        }


@dataclass
class States(ResponseObject):
    """
    Represents a collection of aircraft state vectors from the OpenSky Network.

    This class stores a list of state vectors for multiple aircraft, along with
    a timestamp indicating when the data was collected.

    Attributes:
        time: The seconds since epoch of the last position report. Gives the validity period of all states.
              All vectors represent the state of a vehicle with the interval `[time - 1, time]`.
        states: A list of state vectors of aircraft. None if no states are available.
    """
    time: int
    states: List[StateVector]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'States':
        """
        Create a States object from a dictionary.

        This method converts the raw API response into a States object,
        handling both dictionary and list formats for state vectors.

        Args:
            data: The dictionary to create the States object from.

        Returns:
            A new States instance containing the parsed state vectors.
        """
        return cls(
            time=data['time'],
            states=[
                StateVector.from_dict(state) if isinstance(state, dict) else
                StateVector.from_list(state)
                for state in data['states'] or []
            ]
        )

    def to_geojson(self) -> Dict[str, Any]:
        """
        Convert the states collection to GeoJSON format.

        This method creates a GeoJSON feature collection containing all
        aircraft state vectors.

        Returns:
            A GeoJSON feature collection containing all aircraft states.
        """
        return {
            "type": "FeatureCollection",
            "features": [state.to_geojson() for state in self.states]
        }


@dataclass
class Waypoint(ResponseObject):
    """
    Represents a waypoint in an aircraft's flight track from the OpenSky Network.

    This class stores information about a specific point in an aircraft's flight
    path, including its position, altitude, and timing.

    Attributes:
        time: Time which the given waypoint is associated with in seconds since epoch (Unix time).
        latitude: The WGS-84 latitude in decimal degrees. Can be null.
        longitude: The WGS-84 longitude in decimal degrees. Can be null.
        baro_altitude: The barometric altitude of the waypoint. Can be null.
        true_track: The true track of the waypoint in decimal degrees clockwise from north (north=0°). Can be null.
        on_ground: Whether the waypoint is on the ground (retrieved from a surface position report).
    """
    time: int
    latitude: Optional[float]
    longitude: Optional[float]
    baro_altitude: Optional[float]
    true_track: Optional[float]
    on_ground: bool

    def to_geojson(self) -> Dict[str, Any]:
        """
        Convert the waypoint to GeoJSON format.

        This method creates a GeoJSON feature representing the waypoint's
        position and properties.

        Returns:
            A GeoJSON feature containing the waypoint's position and properties.
        """
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude]
            },
            "properties": {
                "time": self.time,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "baro_altitude": self.baro_altitude,
                "true_track": self.true_track,
                "on_ground": self.on_ground
            }
        }


@dataclass
class FlightTrack(ResponseObject):
    """
    Represents a complete flight track of an aircraft from the OpenSky Network.

    This class stores the entire flight path of an aircraft, including all
    waypoints and timing information.

    Attributes:
        icao24: The ICAO24 address of the transmitter in hex string representation.
        startTime: The seconds since epoch of the start of the flight track.
        endTime: The seconds since epoch of the end of the flight track.
        callsign: The callsign of the vehicle. Can be None if no callsign has been received.
        path: A list of waypoints of the flight track.
    """
    icao24: str
    startTime: int
    endTime: int
    callsign: Optional[str]
    path: List[Waypoint]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FlightTrack':
        """
        Create a FlightTrack object from a dictionary.

        This method converts the raw API response into a FlightTrack object,
        handling both dictionary and list formats for waypoints.

        Args:
            data: The dictionary to create the FlightTrack object from.

        Returns:
            A new FlightTrack instance containing the parsed waypoints.
        """
        return cls(
            icao24=data['icao24'],
            startTime=data['startTime'],
            endTime=data['endTime'],
            callsign=data['callsign'],
            path=[
                Waypoint.from_dict(waypoint) if isinstance(waypoint, dict) else
                Waypoint.from_list(waypoint)
                for waypoint in data['path'] or []
            ]
        )

    def to_geojson(self) -> Dict[str, Any]:
        """
        Convert the flight track to GeoJSON format.

        This method creates a GeoJSON feature representing the complete flight
        path as a LineString, with additional properties.

        Returns:
            A GeoJSON feature containing the flight track as a LineString and properties.
        """
        return {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[waypoint.longitude, waypoint.latitude] for waypoint in self.path]
            },
            "properties": {
                "icao24_code": self.icao24,
                "callsign": self.callsign,
                "start_time": self.startTime,
                "end_time": self.endTime,
            }
        }


class OpenSkyConfig(BaseConfig):
    """
    Configuration class for the OpenSky Network API client.

    This class manages the configuration settings for connecting to the OpenSky
    Network API, including authentication and rate limiting parameters.

    Attributes:
        opensky_base_url: The base URL for the OpenSky API.
        opensky_username: The username for the OpenSky API.
        opensky_password: The password for the OpenSky API.
        opensky_rate_limit_window_no_auth: The rate limit window for the OpenSky API without authentication.
        opensky_rate_limit_window_auth: The rate limit window for the OpenSky API with authentication.
    """
    opensky_base_url: str = Field(
        default="https://opensky-network.org/",
        description="The base URL for the OpenSky API"
    )
    opensky_username: str = Field(
        default="",
        description="The username for the OpenSky API"
    )
    opensky_password: str = Field(
        default="",
        description="The password for the OpenSky API",
        repr=False,
        exclude=True
    )
    opensky_rate_limit_window_no_auth: int = Field(
        default=10,
        description="The rate limit window for the OpenSky API without authentication"
    )
    opensky_rate_limit_window_auth: int = Field(
        default=10,
        description="The rate limit window for the OpenSky API with authentication"
    )


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
            auth=aiohttp.BasicAuth(
                config.opensky_username,
                config.opensky_password
            ) if config.opensky_username else None
        )
        self._last_requests = defaultdict(lambda: 0)
        self._rate_limit_lock = asyncio.Lock()

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
            if self._config.opensky_username
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

        params = {}
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
            params=params,
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
        if not self._config.opensky_username or not self._config.opensky_password:
            raise ValueError("Authentication required for this operation")

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
            params=params,
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
            params=params,
        ) as response:
            data = await self._handle_response(response)
            return FlightTrack.from_dict(data) if data else None
