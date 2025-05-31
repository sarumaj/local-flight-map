"""
OpenSky API module for the Local Flight Map application.
Provides classes and utilities for interacting with the OpenSky Network API to fetch aircraft states,
tracks, and other flight data.
"""

from typing import Optional, List, Any, Dict
from dataclasses import dataclass

from ..base import ResponseObject


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
