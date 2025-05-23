from dataclasses import dataclass
from typing import List, Optional, Union, Dict, Any
from pydantic import Field
from urllib.parse import urlparse
from async_lru import alru_cache
from .base import BaseClient, BaseConfig, ResponseObject, Location


@dataclass
class AircraftProperties(ResponseObject):
    """
    Represents an aircraft from ADSB Exchange API.

    Attributes:
        hex: The ICAO24 address of the transmitter in hex string representation.
        type: The type of the aircraft (e.g., adsb_icao, mlat).
        flight: The callsign of the aircraft. Can be None.
        r: The registration of the aircraft. Can be None.
        t: The type code of the aircraft. Can be None.
        dbFlags: The database flags of the aircraft. Can be None.
        alt_baro: The barometric altitude of the aircraft. Can be "ground" or a number.
        alt_geom: The geometric altitude of the aircraft. Can be None.
        gs: The ground speed of the aircraft in knots. Can be None.
        ias: The indicated airspeed of the aircraft in knots. Can be None.
        tas: The true airspeed of the aircraft in knots. Can be None.
        mach: The Mach number of the aircraft. Can be None.
        wd: The wind direction in degrees. Can be None.
        ws: The wind speed in knots. Can be None.
        oat: The outside air temperature in Celsius. Can be None.
        tat: The total air temperature in Celsius. Can be None.
        track: The track angle in degrees. Can be None.
        track_rate: The rate of change of track angle in degrees per second. Can be None.
        roll: The roll angle in degrees. Can be None.
        mag_heading: The magnetic heading in degrees. Can be None.
        true_heading: The true heading in degrees. Can be None.
        baro_rate: The barometric rate of climb/descent in feet per minute. Can be None.
        geom_rate: The geometric rate of climb/descent in feet per minute. Can be None.
        squawk: The squawk code of the aircraft. Can be None.
        emergency: The emergency status of the aircraft. Can be None.
        category: The category of the aircraft. Can be None.
        nav_qnh: The QNH pressure in hPa. Can be None.
        nav_altitude_mcp: The MCP selected altitude in feet. Can be None.
        nav_altitude_fms: The FMS selected altitude in feet. Can be None.
        nav_heading: The selected heading in degrees. Can be None.
        nav_modes: The navigation modes. Can be None.
        lat: The latitude of the aircraft. Can be None.
        lon: The longitude of the aircraft. Can be None.
        nic: The navigation integrity category. Can be None.
        rc: The radius of containment. Can be None.
        seen_pos: The time since last position update in seconds. Can be None.
        version: The version of the aircraft's ADS-B system. Can be None.
        nic_baro: The barometric navigation integrity category. Can be None.
        nac_p: The navigation accuracy category for position. Can be None.
        nac_v: The navigation accuracy category for velocity. Can be None.
        sil: The surveillance integrity level. Can be None.
        sil_type: The type of surveillance integrity level. Can be None.
        gva: The geometric vertical accuracy. Can be None.
        sda: The system design assurance. Can be None.
        alert: The alert flag. Can be None.
        spi: The special position indicator flag. Can be None.
        mlat: The multilateration sources. Can be None.
        tisb: The TIS-B sources. Can be None.
        messages: The number of messages received. Can be None.
        seen: The time since last update in seconds. Can be None.
        rssi: The received signal strength indicator in dBm. Can be None.
        gpsOkBefore: The time since last GPS update in seconds. Can be None.
        gpsOkLat: The latitude of the GPS update. Can be None.
        gpsOkLon: The longitude of the GPS update. Can be None.
    """
    hex: str
    type: str
    flight: Optional[str]
    r: Optional[str]
    t: Optional[str]
    dbFlags: Optional[int]
    alt_baro: Union[str, int]
    alt_geom: Optional[int]
    gs: Optional[float]
    ias: Optional[float]
    tas: Optional[float]
    mach: Optional[float]
    wd: Optional[float]
    ws: Optional[float]
    oat: Optional[float]
    tat: Optional[float]
    track: Optional[float]
    track_rate: Optional[float]
    roll: Optional[float]
    mag_heading: Optional[float]
    true_heading: Optional[float]
    baro_rate: Optional[float]
    geom_rate: Optional[float]
    squawk: Optional[str]
    emergency: Optional[str]
    category: Optional[str]
    nav_qnh: Optional[float]
    nav_altitude_mcp: Optional[int]
    nav_altitude_fms: Optional[int]
    nav_heading: Optional[float]
    nav_modes: Optional[List[str]]
    lat: Optional[float]
    lon: Optional[float]
    nic: Optional[int]
    rc: Optional[int]
    seen_pos: Optional[float]
    version: Optional[int]
    nic_baro: Optional[int]
    nac_p: Optional[int]
    nac_v: Optional[int]
    sil: Optional[int]
    sil_type: Optional[str]
    gva: Optional[int]
    sda: Optional[int]
    alert: Optional[int]
    spi: Optional[int]
    mlat: Optional[List[str]]
    tisb: Optional[List[str]]
    messages: Optional[int]
    seen: Optional[float]
    rssi: Optional[float]
    gpsOkBefore: Optional[float]
    gpsOkLat: Optional[float]
    gpsOkLon: Optional[float]

    def to_geojson(self) -> Dict[str, Any]:
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    self.gpsOkLon if self.gpsOkLon else self.lon,
                    self.gpsOkLat if self.gpsOkLat else self.lat
                ]
            },
            "properties": {
                "icao24_code": self.hex,
                "callsign": self.flight,
                "registration": self.r,
                "type": self.t,
                "baro_altitude": self.alt_baro,
                "geom_altitude": self.alt_geom,
                "ground_speed": self.gs,
                "indicated_airspeed": self.ias,
                "true_airspeed": self.tas,
                "mach": self.mach,
                "wind_direction": self.wd,
                "wind_speed": self.ws,
                "outside_air_temperature": self.oat,
                "total_air_temperature": self.tat,
                "track_angle": self.track,
                "track_rate": self.track_rate,
                "roll_angle": self.roll,
                "magnetic_heading": self.mag_heading,
                "true_heading": self.true_heading,
                "baro_rate_of_climb_descent": self.baro_rate,
                "geom_rate_of_climb_descent": self.geom_rate,
                "squawk_code": self.squawk,
                "emergency_status": self.emergency,
                "category": self.category,
                "qnh_pressure": self.nav_qnh,
                "mcp_altitude": self.nav_altitude_mcp,
                "fms_altitude": self.nav_altitude_fms,
                "heading": self.nav_heading,
                "navigation_modes": self.nav_modes,
                "latitude": self.lat,
                "longitude": self.lon,
                "navigation_integrity_category": self.nic,
                "radius_of_containment": self.rc,
                "time_since_last_position_update": self.seen_pos,
                "version": self.version,
                "baro_navigation_integrity_category": self.nic_baro,
                "navigation_accuracy_category_for_position": self.nac_p,
                "navigation_accuracy_category_for_velocity": self.nac_v,
                "surveillance_integrity_level": self.sil,
                "surveillance_integrity_level_type": self.sil_type,
                "geometric_vertical_accuracy": self.gva,
                "system_design_assurance": self.sda,
                "alert_flag": self.alert,
                "special_position_indicator_flag": self.spi,
                "multilateration_sources": self.mlat,
                "tisb_sources": self.tisb,
                "number_of_messages_received": self.messages,
                "time_since_last_update": self.seen,
                "received_signal_strength_indicator": self.rssi,
                "time_since_last_gps_update": self.gpsOkBefore,
                "latitude_of_gps_update": self.gpsOkLat,
                "longitude_of_gps_update": self.gpsOkLon
            }
        }


@dataclass
class AdsbExchangeResponse(ResponseObject):
    """
    Represents a response from ADSB Exchange API.

    Attributes:
        ac: List of aircraft data.
        msg: Message from the API.
        now: Current timestamp in milliseconds since epoch.
        total: Total number of aircraft.
        ctime: Client timestamp in milliseconds since epoch.
        ptime: Processing time in milliseconds.
    """
    ac: List[AircraftProperties]
    msg: str
    now: int
    total: int
    ctime: int
    ptime: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdsbExchangeResponse':
        return cls(
            ac=[AircraftProperties.from_dict(aircraft) for aircraft in data['ac']],
            msg=data['msg'],
            now=data['now'],
            total=data['total'],
            ctime=data['ctime'],
            ptime=data['ptime']
        )
    
    def to_geojson(self) -> Dict[str, Any]:
        return {
            "type": "FeatureCollection",
            "features": [aircraft.to_geojson() for aircraft in self.ac]
        }


class AdsbExchangeConfig(BaseConfig):
    """
    Config for the AdsbExchange API.

    Attributes:
        adsbexchange_base_url: The base URL for the AdsbExchange API.
        adsbexchange_api_key: The API key for the AdsbExchange API.
    """
    adsbexchange_base_url: str = Field(
        default="https://adsbexchange-com1.p.rapidapi.com/",
        description="The base URL for the AdsbExchange API"
    )
    adsbexchange_api_key: str = Field(
        default="",
        description="The API key for the AdsbExchange API",
        repr=False,
        exclude=True
    )


class AdsbExchangeClient(BaseClient):
    """
    Client for the AdsbExchange API.
    """
    def __init__(self, config: Optional[AdsbExchangeConfig] = None):
        config = config or AdsbExchangeConfig()
        BaseClient.__init__(
            self,
            config=config,
            base_url=config.adsbexchange_base_url,
            headers={
                'X-RapidAPI-Key': config.adsbexchange_api_key,
                'X-RapidAPI-Host': urlparse(config.adsbexchange_base_url).netloc
            }
        )

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.get_aircraft_from_adsbexchange_by_registration.cache_close()
        await self.get_aircraft_from_adsbexchange_by_icao24.cache_close()
        await self.get_aircraft_from_adsbexchange_by_callsign.cache_close()
        await self.get_aircraft_from_adsbexchange_by_squawk.cache_close()
        await self.get_military_aircrafts_from_adsbexchange.cache_close()
        await self.get_aircraft_from_adsbexchange_within_range.cache_close()
        await super(AdsbExchangeClient, self).__aexit__(exc_type, exc_val, exc_tb)

    @alru_cache(maxsize=1000)
    async def get_aircraft_from_adsbexchange_by_registration(
        self,
        registration: str
    ) -> Optional[AdsbExchangeResponse]:
        """
        Get aircraft information from ADSB Exchange by registration.

        Args:
            registration: The registration of the aircraft.

        Returns:
            Optional[AdsbExchangeResponse]: The aircraft information.
        """
        async with self._session.get("/v2/registration/{registration}".format(
            registration=registration.strip()
        )) as response:
            data = await self._handle_response(response)
            return AdsbExchangeResponse.from_dict(data) or None

    @alru_cache(ttl=1)
    async def get_aircraft_from_adsbexchange_by_icao24(
        self,
        icao24: str
    ) -> Optional[AdsbExchangeResponse]:
        """
        Get aircraft information from ADSB Exchange by ICAO24.

        Args:
            icao24: The ICAO24 of the aircraft.

        Returns:
            Optional[AdsbExchangeResponse]: The aircraft information.
        """
        async with self._session.get("/v2/icao/{icao24}".format(
            icao24=icao24.strip()
        )) as response:
            data = await self._handle_response(response)
            return AdsbExchangeResponse.from_dict(data) if data else None

    @alru_cache(ttl=1)
    async def get_aircraft_from_adsbexchange_by_callsign(
        self,
        callsign: str
    ) -> Optional[AdsbExchangeResponse]:
        """
        Get aircraft information from ADSB Exchange by callsign.

        Args:
            callsign: The callsign of the aircraft.

        Returns:
            Optional[AdsbExchangeResponse]: The aircraft information.
        """
        async with self._session.get("/v2/callsign/{callsign}".format(
            callsign=callsign.lower().strip()
        )) as response:
            data = await self._handle_response(response)
            return AdsbExchangeResponse.from_dict(data) if data else None

    @alru_cache(ttl=1)
    async def get_aircraft_from_adsbexchange_by_squawk(
        self,
        squawk: str
    ) -> Optional[AdsbExchangeResponse]:
        """
        Get aircraft information from ADSB Exchange by squawk.

        Args:
            squawk: The squawk of the aircraft.

        Returns:
            Optional[AdsbExchangeResponse]: The aircraft information.
        """
        async with self._session.get("/v2/sqk/{squawk}".format(
            squawk=squawk.strip()
        )) as response:
            data = await self._handle_response(response)
            return AdsbExchangeResponse.from_dict(data) if data else None

    @alru_cache(ttl=1)
    async def get_military_aircrafts_from_adsbexchange(
        self,
    ) -> Optional[AdsbExchangeResponse]:
        """
        Get military aircrafts from ADSB Exchange.

        Returns:
            Optional[AdsbExchangeResponse]: The military aircrafts information.
        """
        async with self._session.get("/v2/mil") as response:
            data = await self._handle_response(response)
            return AdsbExchangeResponse.from_dict(data) if data else None

    @alru_cache(ttl=1)
    async def get_aircraft_from_adsbexchange_within_range(
        self,
        center: Location,
        radius: int
    ) -> Optional[AdsbExchangeResponse]:
        """
        Get aircraft information from ADSB Exchange within a range.

        Args:
            center: The center of the range.
            radius: The radius of the range in nautical miles.

        Returns:
            Optional[AdsbExchangeResponse]: The aircraft information.
        """
        async with self._session.get("/v2/lat/{lat}/lon/{lon}/dist/{radius}".format(
            lat=center.latitude,
            lon=center.longitude,
            radius=radius
        )) as response:
            data = await self._handle_response(response)
            return AdsbExchangeResponse.from_dict(data) if data else None
