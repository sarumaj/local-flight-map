import panel as pn
import folium
from folium.plugins import MarkerCluster
from PIL import Image
import io
import base64
from pathlib import Path
from typing import Union, NamedTuple
from fasthtml.common import Div, H3,  Table, Th, Tr, Td
import asyncio

from ..api.base import Location, BBox
from ..api.adsbexchange import AircraftProperties
from ..api.hexdb import AircraftInformation, RouteInformation
from ..api.opensky import StateVector
from ..api import ApiClient, ApiConfig


class StandardizedAircraft(NamedTuple):
    icao24: str
    callsign: str
    origin_country: str
    latitude: float
    longitude: float
    velocity: float
    direction: float
    vertical_rate: float
    baro_altitude: float
    geo_altitude: float
    type: str
    manufacturer: str
    route: str

    @classmethod
    def standardize_aircraft(
        cls, aircraft:
        Union[StateVector, AircraftProperties],
        aircraft_information: AircraftInformation,
        route_information: RouteInformation,
    ) -> 'StandardizedAircraft':
        if isinstance(aircraft, StateVector):
            return StandardizedAircraft(
                icao24=aircraft.icao24,
                callsign=aircraft.callsign.strip() if aircraft.callsign else 'unknown',
                origin_country=aircraft.origin_country,
                latitude=aircraft.latitude,
                longitude=aircraft.longitude,
                velocity=aircraft.velocity,
                direction=aircraft.true_track,
                vertical_rate=aircraft.vertical_rate,
                baro_altitude=aircraft.baro_altitude,
                geo_altitude=aircraft.geo_altitude,
                type=aircraft_information.Type if aircraft_information else None,
                manufacturer=aircraft_information.Manufacturer if aircraft_information else None,
                route=route_information.Route if route_information else None,
            )
        elif isinstance(aircraft, AircraftProperties):
            return StandardizedAircraft(
                icao24=aircraft.hex,
                callsign=aircraft.flight,
                origin_country="",
                latitude=aircraft.lat,
                longitude=aircraft.lon,
                velocity=aircraft.gs,
                direction=aircraft.true_heading,
                vertical_rate=aircraft.baro_rate,
                baro_altitude=aircraft.alt_baro,
                geo_altitude=aircraft.alt_geom,
                type=aircraft_information.Type if aircraft_information else None,
                manufacturer=aircraft_information.Manufacturer if aircraft_information else None,
                route=route_information.Route if route_information else None,
            )


class RotatedIcon(folium.DivIcon):
    def __init__(self, image_path: str, rotation_angle: float = 0):
        """
        Initialize a rotated icon for aircraft markers.

        Args:
            image_path: Path to the aircraft icon image
            rotation_angle: Rotation angle in degrees (0 = North, 90 = East)
        """
        with Image.open(image_path) as img:
            img = img.convert('RGBA')
            rotated_img = img.rotate(-rotation_angle, expand=True, resample=Image.Resampling.BICUBIC)

            buffered = io.BytesIO()
            rotated_img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            icon_html = f'<img src="data:image/png;base64,{img_str}" style="width:100%;height:100%;">'

            super().__init__(
                html=icon_html,
                icon_size=(48, 48),
                icon_anchor=(24, 24)
            )


class PlaneMarker(folium.Marker):
    def __init__(
        self,
        aircraft: StandardizedAircraft,
        icon_path: str = Path(__file__).parent / "icons" / "civilian_plane.png",
        icon_angle: float = 45,
    ):
        """
        Initialize a plane marker with a rotatable icon.

        Args:
            state_vector: StateVector object containing aircraft data
            aircraft_information: AircraftInformation object containing aircraft information
            icon_path: Path to the aircraft icon image
            icon_angle: Angle of the icon
        """
        self._icon_path = icon_path
        self._icon_angle = icon_angle
        self._aircraft = aircraft

        desc_props = {
            "ICAO ID": self._aircraft.icao24,
        }

        if self._aircraft.callsign:
            desc_props["Callsign"] = self._aircraft.callsign

        if self._aircraft.origin_country:
            desc_props["Origin"] = self._aircraft.origin_country

        if self._aircraft.latitude and self._aircraft.longitude:
            desc_props["Position"] = (
                f"{round(self._aircraft.latitude, 2):,.2f}°N, "
                f"{round(self._aircraft.longitude, 2):,.2f}°E"
            )

        if self._aircraft.velocity:
            desc_props["Ground Speed"] = (
                f"{round(self._aircraft.velocity, 2):,.2f} m/s "
                f"({round(self._aircraft.velocity * 1.94384, 2):,.2f} kts)"
            )

        if self._aircraft.vertical_rate:
            desc_props["Vertical Rate"] = (
                f"{round(self._aircraft.vertical_rate, 2):,.2f} m/s "
                f"({round(self._aircraft.vertical_rate * 196.8503937007874, 2):,.2f} ft/min)"
            )

        if self._aircraft.baro_altitude:
            desc_props["Baro Altitude"] = (
                f"{round(self._aircraft.baro_altitude, 2):,.2f} m "
                f"({round(self._aircraft.baro_altitude * 3.28084, 2):,.2f} ft)"
            ) if self._aircraft.baro_altitude != "ground" else self._aircraft.baro_altitude

        if self._aircraft.geo_altitude:
            desc_props["Geo Altitude"] = (
                f"{round(self._aircraft.geo_altitude, 2):,.2f} m "
                f"({round(self._aircraft.geo_altitude * 3.28084, 2):,.2f} ft)"
            ) if self._aircraft.geo_altitude != "ground" else self._aircraft.geo_altitude

        if self._aircraft.type:
            desc_props["Type"] = self._aircraft.type

        if self._aircraft.manufacturer:
            desc_props["Manufacturer"] = self._aircraft.manufacturer

        self._description = Div(
            H3("Aircraft Information"),
            Table(*[
                Tr(Th(key), Td(value)) for key, value in desc_props.items()
            ])
        )
        super().__init__(
            location=(self._aircraft.latitude, self._aircraft.longitude),
            popup=folium.Popup(html=str(self._description), max_width=200),
            tooltip=folium.Tooltip(str(self._description)),
            icon=RotatedIcon(icon_path, (self._aircraft.direction or 0) - self._icon_angle)
        )


class MapInterface:
    def __init__(self, center: Location, zoom: int = 12):
        self.center = center
        self.zoom = zoom
        self.map = folium.Map(
            location=(center.latitude, center.longitude),
            zoom_start=zoom,
        )
        self.additional_tiles = [
            folium.TileLayer(
                name="OPNVKarte",
                tiles='https://tileserver.memomaps.de/tilegen/{z}/{x}/{y}.png',
                attr=(
                    'Map <a href="https://memomaps.de/">memomaps.de</a> '
                    '<a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, map data &copy; '
                    '<a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                ),
                max_zoom=18
            )
        ]
        for tile in self.additional_tiles:
            tile.add_to(self.map)
        self.mouse_position = folium.plugins.MousePosition(
            position="topright",
            separator=", ",
            empty_string="NaN",
            num_digits=20,
            prefix="Coordinates:",
            lat_formatter="function(num) {return L.Util.formatNum(num, 3) + '&deg;N';};",
            lng_formatter="function(num) {return L.Util.formatNum(num, 3) + '&deg;E';};",
        )
        self.mouse_position.add_to(self.map)
        self.cluster_group = MarkerCluster(control=False)
        self.cluster_group.add_to(self.map)
        self.control_layer = folium.LayerControl()
        self.control_layer.add_to(self.map)

    def add_plane_marker(self, plane_marker: folium.Marker):
        plane_marker.add_to(self.cluster_group)

    def add_flight_track(self, flight_track: folium.PolyLine):
        flight_track.add_to(self.map)

    def draw_bbox(self, bbox: BBox):
        """
        Draw a bounding box on the map as a rectangle.

        Args:
            bbox: BBox object containing the bounding box coordinates
        """
        # Create a rectangle by connecting the corners in the correct order
        folium.PolyLine(
            locations=[
                (bbox.min_lat, bbox.min_lon),  # Southwest corner
                (bbox.min_lat, bbox.max_lon),  # Southeast corner
                (bbox.max_lat, bbox.max_lon),  # Northeast corner
                (bbox.max_lat, bbox.min_lon),  # Northwest corner
                (bbox.min_lat, bbox.min_lon),  # Back to Southwest corner to close the rectangle
            ],
            color="red",
            weight=2,
            opacity=0.7
        ).add_to(self.map)

    def create_map_widget(self):
        map_pane = pn.pane.plot.Folium(self.map, sizing_mode="stretch_both")
        return map_pane

    def serve(self, port: int = 5006):
        return pn.serve(self.create_map_widget(), port=port)


async def amain(map_interface: MapInterface, radius: float = 100):
    config = ApiConfig()
    async with ApiClient(config) as client:
        bbox = BBox.get_bbox_by_radius(map_interface.center, radius)
        map_interface.draw_bbox(bbox)
        states = await client.get_aircraft_from_adsbexchange_within_range(map_interface.center, radius)
        for state in states.ac:
            aircraft_info = await client.get_aircraft_information_from_hexdb(state.hex)
            route_info = await client.get_route_information_from_hexdb(state.hex)
            standardized_aircraft = StandardizedAircraft.standardize_aircraft(state, aircraft_info, route_info)
            print(standardized_aircraft, state, aircraft_info, route_info, end="\n\n", sep="\n")
            if standardized_aircraft.longitude is not None and standardized_aircraft.latitude is not None:
                map_interface.add_plane_marker(PlaneMarker(standardized_aircraft))

if __name__ == "__main__":
    map_interface = MapInterface(Location(50.15, 8.3166667), 12)
    asyncio.run(amain(map_interface))
    map_interface.serve()
