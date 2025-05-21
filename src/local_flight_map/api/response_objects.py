from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
import json
from itertools import zip_longest


class ResponseObject:
    """
    Base class for all response objects.
    """
    __annotations__: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResponseObject':
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'ResponseObject':
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def from_list(cls, data: List[Any]) -> 'ResponseObject':
        return cls.from_dict(dict(zip_longest(cls.__annotations__.keys(), data)))


@dataclass
class AircraftInformation(ResponseObject):
    """
    Represents information about an aircraft.

    Attributes:
        ICAOTypeCode: The ICAO type code of the aircraft.
        Manufacturer: The manufacturer of the aircraft.
        ModeS: The Mode S code of the aircraft.
        OperatorFlagCode: The operator flag code of the aircraft.
        RegisteredOwners: The registered owners of the aircraft.
        Registration: The registration of the aircraft.
        Type: The type of the aircraft.
    """
    ICAOTypeCode: str
    Manufacturer: str
    ModeS: str
    OperatorFlagCode: str
    RegisteredOwners: str
    Registration: str
    Type: str


@dataclass
class RouteInformation(ResponseObject):
    """
    Represents information about a route.

    Attributes:
        flight: The flight number of the route.
        route: The route of the flight.
        update_time: The time of the update of the route in seconds since epoch (Unix time).
    """
    flight: str
    route: str
    updatetime: int


@dataclass
class AirportInformation(ResponseObject):
    """
    Represents information about an airport.

    Attributes:
        airport: The airport code of the airport.
        country_code: The country code of the airport.
        iata: The IATA code of the airport.
        icao: The ICAO code of the airport.
        latitude: The latitude of the airport.
        longitude: The longitude of the airport.
        region_name: The region name of the airport.
    """
    airport: str
    country_code: str
    iata: str
    icao: str
    latitude: float
    longitude: float
    region_name: str


@dataclass
class StateVector(ResponseObject):
    """
    Represents a state vector of an aircraft.

    Attributes:
        icao24:             The ICAO24 address of the transmitter in hex string representation.
        callsign:           The callsign of the vehicle. Can be None if no callsign has been received.
        origin_country:     The country inferred through the ICAO24 address.
        time_position:      The seconds since epoch of last position report.
                            Can be None if there was no position report received by OpenSky within 15s
                            before the current time.
        last_contact:       The last time the aircraft was in contact with the system.
        longitude:          The longitude of the aircraft. Can be None.
        latitude:           The latitude of the aircraft. Can be None.
        baro_altitude:      The barometric altitude of the aircraft. Can be None.
        on_ground:          Whether the aircraft is on the ground (the vehicle sends ADS-B surface position reports).
        velocity:           The velocity of the aircraft over ground in m/s. Can be None.
        true_track:         The true track of the aircraft in decimal degrees (0 is north). Can be None.
        vertical_rate:      The vertical rate of the aircraft in m/s, incline is positive, decline negative.
                            Can be None.
        sensors:            The serial numbers of sensors which received messages from the vehicle within the validity
                            period of this state vector. Can be None if no filtering for sensor has been requested.
        geo_altitude:       The geometric altitude of the aircraft in meters. Can be None.
        squawk:             The squawk code of the aircraft. Can be None.
        spi:                Whether the aircraft is in special position indication mode.
        position_source:    The source of the position data:
                                0 = ADS-B,
                                1 = ASTERIX,
                                2 = MLAT,
                                3 = FLARM.
        category:           The category of the aircraft:
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


@dataclass
class States(ResponseObject):
    """
    Represents a list of state vectors of aircraft.

    Attributes:
        time:   The seconds since epoch of the last position report. Gives the validity period of all states.
                All vectors represent the state of a vehicle with the interval `[time - 1, time]`.
        states: A list of state vectors of aircraft. None if no states are available.
    """
    time: int
    states: List[StateVector]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'States':
        return cls(
            time=data['time'],
            states=[
                StateVector.from_dict(state) if isinstance(state, dict) else
                StateVector.from_list(state)
                for state in data['states'] or []
            ]
        )


@dataclass
class Waypoint(ResponseObject):
    """
    Represents a waypoint of an aircraft.

    Attributes:
        time:           Time which the given waypoint is associated with in seconds since epoch (Unix time).
        latitude:       The WGS-84 latitude in decimal degrees. Can be null.
        longitude:      The WGS-84 longitude in decimal degrees. Can be null.
        baro_altitude:  The barometric altitude of the waypoint. Can be null.
        true_track:     The true track of the waypoint in decimal degrees clockwise from north (north=0°). Can be null.
        on_ground:      Whether the waypoint is on the ground (retrieved from a surface position report).
    """
    time: int
    latitude: Optional[float]
    longitude: Optional[float]
    baro_altitude: Optional[float]
    true_track: Optional[float]
    on_ground: bool


@dataclass
class FlightTrack(ResponseObject):
    """
    Represents a flight track of an aircraft.

    Attributes:
        icao24:     The ICAO24 address of the transmitter in hex string representation.
        startTime:  The seconds since epoch of the start of the flight track.
        endTime:    The seconds since epoch of the end of the flight track.
        callsign:   The callsign of the vehicle. Can be None if no callsign has been received.
        path:       A list of waypoints of the flight track.
    """
    icao24: str
    startTime: int
    endTime: int
    callsign: Optional[str]
    path: List[Waypoint]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FlightTrack':
        return cls(
            icao24=data['icao24'],
            startTime=data['startTime'],
            endTime=data['endTime'],
            callsign=data['callsign'],
            path=[
                Waypoint.from_dict(waypoint) if isinstance(waypoint, dict) else
                Waypoint.from_list(waypoint)
                for waypoint in data['path']
            ]
        )
