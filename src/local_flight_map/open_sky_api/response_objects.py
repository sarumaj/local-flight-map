from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
import json
from itertools import zip_longest


@dataclass
class StateVector:
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

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateVector':
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'StateVector':
        return cls.from_dict(json.loads(json_str))
    
    @classmethod 
    def from_list(cls, data: List[Dict[str, Any]]) -> 'StateVector':
        return cls.from_dict(dict(zip_longest(cls.__annotations__.keys(), data)))

@dataclass
class OpenSkyStates:
    time: int
    states: List[StateVector]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'time': self.time,
            'states': [state.to_dict() for state in self.states]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OpenSkyStates':
        return cls(
            time=data['time'],
            states=[StateVector.from_dict(state) for state in data['states']]
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'OpenSkyStates':
        return cls.from_dict(json.loads(json_str))


@dataclass
class Waypoint:
    time: int
    latitude: Optional[float]
    longitude: Optional[float]
    baro_altitude: Optional[float]
    true_track: Optional[float]
    on_ground: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Waypoint':
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'Waypoint':
        return cls.from_dict(json.loads(json_str))
    
    @classmethod
    def from_list(cls, data: List[Dict[str, Any]]) -> 'Waypoint':
        return cls.from_dict(dict(zip_longest(cls.__annotations__.keys(), data)))


@dataclass
class FlightTrack:
    icao24: str
    start_time: int
    end_time: int
    callsign: Optional[str]
    path: List[Waypoint]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'icao24': self.icao24,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'callsign': self.callsign,
            'path': [waypoint.to_dict() for waypoint in self.path]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FlightTrack':
        return cls(
            icao24=data['icao24'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            callsign=data['callsign'],
            path=[Waypoint.from_dict(waypoint) for waypoint in data['path']]
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'FlightTrack':
        return cls.from_dict(json.loads(json_str))