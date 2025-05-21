import panel as pn
import folium
from folium.plugins import MarkerCluster
from PIL import Image
import io
import base64
from pathlib import Path
from fasthtml.common import Div, H3,  Table, Th, Tr, Td
import asyncio

from ..api.response_objects import StateVector, AircraftInformation
from ..api.client import ApiClient
from ..api.config import ApiConfig
from ..api.request_params import BBox, Center


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
        state_vector: StateVector,
        aircraft_information: AircraftInformation,
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
        self._state_vector = state_vector
        self._description = Div(
            H3("Aircraft Information"),
            Table(*[
                Tr(Th(key), Td(value)) for key, value in {
                    "ICAO ID": state_vector.icao24,
                    "Callsign": state_vector.callsign.strip() if state_vector.callsign else 'unknown',
                    "Origin": state_vector.origin_country,
                    "Position": (
                        f"{round(state_vector.latitude, 2):,.2f}°N, "
                        f"{round(state_vector.longitude, 2):,.2f}°E"
                        if state_vector.latitude and state_vector.longitude else 'unknown'
                    ),
                    "Ground Speed": (
                        f"{round(state_vector.velocity, 2):,.2f} m/s "
                        f"({round(state_vector.velocity * 1.94384, 2):,.2f} kts)"
                        if state_vector.velocity else 'unknown'
                    ),
                    "Vertical Rate": (
                        f"{round(state_vector.vertical_rate, 2):,.2f} m/s "
                        f"({round(state_vector.vertical_rate * 196.8503937007874, 2):,.2f} ft/min)"
                        if state_vector.vertical_rate else 'unknown'
                    ),
                    "Baro Altitude": (
                        f"{round(state_vector.baro_altitude, 2):,.2f} m "
                        f"({round(state_vector.baro_altitude * 3.28084, 2):,.2f} ft)"
                        if state_vector.baro_altitude else 'unknown'
                    ),
                    "Geo Altitude": (
                        f"{round(state_vector.geo_altitude, 2):,.2f} m "
                        f"({round(state_vector.geo_altitude * 3.28084, 2):,.2f} ft)"
                        if state_vector.geo_altitude else 'unknown'
                    ),
                }.items()
            ])
        )
        super().__init__(
            location=(state_vector.latitude, state_vector.longitude),
            popup=folium.Popup(html=str(self._description), max_width=200),
            tooltip=folium.Tooltip(str(self._description)),
            icon=RotatedIcon(icon_path, (self._state_vector.true_track or 0) - self._icon_angle)
        )


class MapInterface:
    def __init__(self, center: Center, zoom: int = 12):
        self.center = center
        self.zoom = zoom
        self.map = folium.Map(
            location=(center.latitude, center.longitude),
            zoom_start=zoom,
        )
        self.addtional_tiles = [
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
        for tile in self.addtional_tiles:
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


async def amain(map_interface: MapInterface, radius: float = 1500):
    config = ApiConfig()
    async with ApiClient(config) as client:
        bbox = BBox.get_bbox_by_radius(map_interface.center, radius)
        map_interface.draw_bbox(bbox)
        states = await client.get_states(bbox=bbox)
        for state in states.states:
            if state.longitude is not None and state.latitude is not None:
                map_interface.add_plane_marker(PlaneMarker(state, None))

if __name__ == "__main__":
    map_interface = MapInterface(Center(50.15, 8.3166667), 12)
    asyncio.run(amain(map_interface))
    map_interface.serve()
