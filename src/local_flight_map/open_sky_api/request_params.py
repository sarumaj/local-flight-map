from typing import TypedDict, Optional


class StatesRequestParams(TypedDict):
    time: int
    icao24: str
    lamin: float
    lamax: float
    lomin: float
    lomax: float

class MyStatesRequestParams(TypedDict):
    time: int
    icao24: str
    serials: str

class TrackRequestParams(TypedDict):
    icao24: str
    time: int