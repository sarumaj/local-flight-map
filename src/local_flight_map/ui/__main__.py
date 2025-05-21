import panel as pn
import folium
from folium.plugins import MarkerCluster
from PIL import Image
import io
import base64
from pathlib import Path

from ..open_sky_api.response_objects import StateVector

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
            icon_path: str = Path(__file__).parent / "icons" / "civilian_plane.png",
            initial_heading: float = 45,
        ):
        """
        Initialize a plane marker with a rotatable icon.
        
        Args:
            state_vector: StateVector object containing aircraft data
            icon_path: Path to the aircraft icon image
        """
        self._icon_path = icon_path
        self._initial_heading = initial_heading
        self._state_vector = state_vector
        
        super().__init__(
            location=(state_vector.latitude, state_vector.longitude),
            popup=folium.Popup(html="Plane", max_width=200),
            tooltip=folium.Tooltip(f"Plane {state_vector.true_track}°"),
            icon=RotatedIcon(icon_path, self._state_vector.true_track - self._initial_heading)
        )

class FlightTrack:
    def __init__(self, points: list[tuple[float, float]]):
        self.points = points

class MapInterface:
    def __init__(self, center: tuple[float, float], zoom: int = 12):
        self.center = center
        self.zoom = zoom
        self.map = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles=folium.TileLayer(
                name="OPNVKarte",
                tiles='https://tileserver.memomaps.de/tilegen/{z}/{x}/{y}.png',
                attr=(
                    'Map <a href="https://memomaps.de/">memomaps.de</a> '
                    '<a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, map data &copy; '
                    '<a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                ),
                max_zoom=18
            )
        )
        self.cluster_group = MarkerCluster(control=False)
        self.cluster_group.add_to(self.map)
        self.control_layer = folium.LayerControl()
        self.control_layer.add_to(self.map)

    def add_plane_marker(self, plane_marker: folium.Marker):
        plane_marker.add_to(self.cluster_group)
    
    def add_flight_track(self, flight_track: folium.PolyLine):
        flight_track.add_to(self.map)
    
    def get_map(self):
        return self.map
    
    def create_map_widget(self):
        return pn.pane.plot.Folium(self.map, sizing_mode="stretch_both")
        
    def serve(self, port: int = 5006):
        return pn.serve(self.create_map_widget(), port=port)
    
if __name__ == "__main__":
    # Example usage
    center = (48.208492, 16.372504)  # Vienna
    zoom = 12
    map_interface = MapInterface(center, zoom)

    # Add a sample aerodrome
    plane_marker = PlaneMarker(
        StateVector(
            icao24="A12345",
            sensors=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            latitude=48.208492,
            longitude=16.372504,
            true_track=0,
            callsign="A12345",
            origin_country="AT",
            on_ground=False,
            velocity=100,
            vertical_rate=30,
            baro_altitude=10000,
            geo_altitude=10000,
            squawk="1234",
            spi=False,
            position_source=1,
            category=1,
            last_contact=1716211200,
            time_position=1716211200
        ),
    )

    map_interface.add_plane_marker(plane_marker)

    # Add a sample flight track
    # flight_track = FlightTrack(
    #     points=[
    #         (48.208492, 16.372504),
    #         (48.210000, 16.370000),
    #         (48.211000, 16.368000),
    #         (48.212000, 16.366000),
    #         (48.213000, 16.364000),
    #         (48.214000, 16.362000),
    #         (48.215000, 16.360000)
    #     ]
    # )
    # map_interface.add_flight_track(flight_track)

    # Serve the map
    map_interface.serve()
    
    
    
    
    
