import panel as pn
import folium
from folium.plugins import MarkerCluster
from PIL import Image
import io
import base64
from pathlib import Path
from typing import Union, NamedTuple, Dict, Any
from fasthtml.common import Div, H3,  Table, Th, Tr, Td
import asyncio
import fastapi
from fastapi.staticfiles import StaticFiles
from panel.io.fastapi import add_applications
import uvicorn

from ..api.base import Location, BBox
from ..api import ApiClient, ApiConfig


class MapInterface:
    app: fastapi.FastAPI = fastapi.FastAPI()

    def __init__(self, *, center: Location, zoom: int = 12, radius: float = 50, client: ApiClient):
        self.center = center
        self.zoom = zoom
        self.radius = radius
        self.client = client
        self.map = folium.Map(
            location=(center.latitude, center.longitude),
            zoom_start=zoom,
        )
        # Mount static files directory
        self.app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")
        self.app.add_api_route("/aircrafts", self.get_aircrafts_geojson, methods=["GET"])
        self.additional_tiles = [
            folium.TileLayer(
                name="OPNVKarte",
                tiles='https://tileserver.memomaps.de/tilegen/{z}/{x}/{y}.png',
                attr=(
                    'Map <a href="https://memomaps.de/">memomaps.de</a> '
                    '<a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, map data &copy; '
                    '<a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                )
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
        #self.control_layer = folium.LayerControl()
        #self.control_layer.add_to(self.map)
        self.realtime = folium.plugins.Realtime(
            folium.JsCode("""
                function(responseHandler, errorHandler) {
                    var url = '/aircrafts';

                    fetch(url)
                    .then((response) => {
                        return response.json().then((data) => {
                            return data;
                        })
                    })
                    .then(responseHandler)
                    .catch(errorHandler);
                }
            """),
            get_feature_id=folium.JsCode("(f) => { return f.properties.icao24_code }"),
            point_to_layer=folium.JsCode("""
                function(feature, latlng) {
                    // Create a custom icon with rotation
                    var icon = L.divIcon({
                        className: 'rotated-icon',
                        html: `<img src="/static/icons/civilian_plane.png" style="width:48px;height:48px;transform:rotate(${(feature.properties.track_angle || 0) - 45}deg);">`,
                        iconSize: [48, 48],
                        iconAnchor: [24, 24]
                    });

                    // Create the marker with the custom icon
                    var marker = L.marker(latlng, {icon: icon});

                    // Create popup content
                    var popupContent = '<div class="aircraft-info"><h3>Aircraft Information</h3><table>';
                    for (var key in feature.properties) {
                        popupContent += `<tr><th>${key}</th><td>${feature.properties[key]}</td></tr>`;
                    }
                    popupContent += '</table></div>';

                    // Add popup and tooltip
                    marker.bindPopup(popupContent, {maxWidth: 200});
                    marker.bindTooltip(popupContent);

                    return marker;
                }
            """),
            container=self.cluster_group,
            interval=1000,
        )
        self.realtime.add_to(self.map)
        self.draw_bbox(BBox.get_bbox_by_radius(self.center, self.radius))

    async def get_aircrafts_geojson(self):
        print("Getting aircrafts geojson")
        states = await self.client.get_aircraft_from_adsbexchange_within_range(self.center, self.radius)
        states_geojson = states.to_geojson()
        for index, state_geojson in enumerate(states_geojson["features"]):
            aircraft_info = await self.client.get_aircraft_information_from_hexdb(state_geojson["properties"]["icao24_code"])
            if aircraft_info is not None:
                aircraft_info.patch_geojson_properties(state_geojson)
            route_info = await self.client.get_route_information_from_hexdb(state_geojson["properties"]["icao24_code"])
            if route_info is not None:
                route_info.patch_geojson_properties(state_geojson)
            states_geojson["features"][index] = state_geojson
        return states_geojson

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

    async def serve(self, port: int = 5006):
        add_applications({"/": self.create_map_widget()}, app=self.app, title="Local Flight Map")
        config = uvicorn.Config(self.app, host="0.0.0.0", port=port)
        server = uvicorn.Server(config)
        await server.serve()


async def amain():
    config = ApiConfig()
    async with ApiClient(config) as client:
        map_interface = MapInterface(center=Location(50.15, 8.3166667), zoom=12, radius=50, client=client)
        await map_interface.serve()

if __name__ == "__main__":
    asyncio.run(amain())
