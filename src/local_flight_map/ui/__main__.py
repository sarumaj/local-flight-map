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
                    var icon = L.divIcon({
                        className: 'rotated-icon',
                        html: `
                            <div style="position: relative; width: 48px; height: 48px; cursor: pointer;">
                                <img src="/static/icons/civilian_plane.png" style="width:48px;height:48px;transform:rotate(${(feature.properties.track_angle || 0) - 45}deg); pointer-events: none;">
                                <div style="position: absolute; top: -8px; left: -8px; right: -8px; bottom: -8px; z-index: 1000;"></div>
                            </div>
                        `,
                        iconSize: [48, 48],
                        iconAnchor: [24, 24]
                    });

                    var marker = L.marker(latlng, {
                        icon: icon,
                        interactive: true,
                        riseOnHover: true,
                        autoPanOnFocus: true,
                        keyboard: true,
                        title: feature.properties.icao24_code || 'Aircraft'
                    });

                    // Create popup content function to avoid recreating HTML
                    function createPopupContent(props) {
                        var content = `
                            <div class="aircraft-info" style="max-height: 300px; overflow-y: auto;">
                                <h3 style="margin: 0 0 10px 0; padding: 5px; background: #f8f9fa; position: sticky; top: 0;">Aircraft Information</h3>
                                <table style="width: 100%; border-collapse: collapse;">
                                    <tbody>`;
                        for (var key in props) {
                            content += `
                                <tr style="border-bottom: 1px solid #eee;">
                                    <th style="text-align: left; padding: 5px; background: #f8f9fa;">${key}</th>
                                    <td style="padding: 5px;">${props[key]}</td>
                                </tr>`;
                        }
                        content += `
                                    </tbody>
                                </table>
                            </div>`;
                        return content;
                    }

                    var popup = L.popup({
                        maxWidth: 300,
                        closeButton: true,
                        autoClose: true,
                        closeOnEscapeKey: true,
                        closeOnClick: false
                    });

                    // Store the popup content function on the marker
                    marker._updatePopupContent = function(props) {
                        popup.setContent(createPopupContent(props));
                    };

                    // Initial popup content
                    marker._updatePopupContent(feature.properties);
                    marker.bindPopup(popup);
                    marker.bindTooltip(createPopupContent(feature.properties));

                    // Add click handler directly to the marker
                    marker.on('click', function(e) {
                        e.originalEvent.stopPropagation();
                        if (!popup.isOpen()) {
                            popup.openOn(marker);
                        }
                    });

                    return marker;
                }
            """),
            update_feature=folium.JsCode("""
                function(feature, oldLayer) {
                    if (!oldLayer) { return; }

                    // Store popup state
                    var popup = oldLayer.getPopup();
                    var wasPopupOpen = popup && popup.isOpen();
                    var scrollPosition = 0;
                    if (wasPopupOpen) {
                        var popupElement = popup.getElement();
                        if (popupElement) {
                            var scrollContainer = popupElement.querySelector('.aircraft-info');
                            if (scrollContainer) {
                                scrollPosition = scrollContainer.scrollTop;
                            }
                        }
                    }

                    // Update popup content without recreating the popup
                    if (oldLayer._updatePopupContent) {
                        oldLayer._updatePopupContent(feature.properties);
                    }

                    // Update the layer position with animation
                    var type = feature.geometry && feature.geometry.type;
                    var coordinates = feature.geometry && feature.geometry.coordinates;
                    switch (type) {
                        case 'Point':
                            var newLatLng = L.GeoJSON.coordsToLatLng(coordinates);
                            var currentLatLng = oldLayer.getLatLng();
                            
                            // Animate the marker movement
                            if (currentLatLng) {
                                var duration = 100; // 1 second animation
                                var startTime = null;
                                var startLat = currentLatLng.lat;
                                var startLng = currentLatLng.lng;
                                var endLat = newLatLng.lat;
                                var endLng = newLatLng.lng;
                                
                                function animate(timestamp) {
                                    if (!startTime) startTime = timestamp;
                                    var progress = Math.min((timestamp - startTime) / duration, 1);
                                    
                                    // Easing function for smooth animation
                                    progress = progress < 0.5 ? 4 * progress * progress * progress : 1 - Math.pow(-2 * progress + 2, 3) / 2;
                                    
                                    var currentLat = startLat + (endLat - startLat) * progress;
                                    var currentLng = startLng + (endLng - startLng) * progress;
                                    
                                    oldLayer.setLatLng([currentLat, currentLng]);
                                    
                                    // Update icon rotation
                                    var icon = oldLayer.getIcon();
                                    if (icon && feature.properties.track_angle) {
                                        var newIcon = L.divIcon({
                                            className: 'rotated-icon',
                                            html: `<img src="/static/icons/civilian_plane.png" style="width:48px;height:48px;transform:rotate(${feature.properties.track_angle - 45}deg);">`,
                                            iconSize: [48, 48],
                                            iconAnchor: [24, 24]
                                        });
                                        oldLayer.setIcon(newIcon);
                                    }
                                    
                                    if (progress < 1) {
                                        requestAnimationFrame(animate);
                                    }
                                }
                                
                                requestAnimationFrame(animate);
                            } else {
                                oldLayer.setLatLng(newLatLng);
                            }
                            break;
                        case 'LineString':
                        case 'MultiLineString':
                            oldLayer.setLatLngs(L.GeoJSON.coordsToLatLngs(coordinates, type === 'LineString' ? 0 : 1));
                            break;
                        case 'Polygon':
                        case 'MultiPolygon':
                            oldLayer.setLatLngs(L.GeoJSON.coordsToLatLngs(coordinates, type === 'Polygon' ? 1 : 2));
                            break;
                        default:
                            return null;
                    }

                    // Restore popup state
                    if (wasPopupOpen) {
                        // Ensure popup is open
                        if (!popup.isOpen()) {
                            popup.openOn(oldLayer);
                        }
                        
                        // Restore scroll position
                        var popupElement = popup.getElement();
                        if (popupElement) {
                            var scrollContainer = popupElement.querySelector('.aircraft-info');
                            if (scrollContainer) {
                                scrollContainer.scrollTop = scrollPosition;
                            }
                        }
                    }

                    return oldLayer;
                }
            """),
            container=self.cluster_group,
            interval=100,
            showControl=False
        )
        self.realtime.add_to(self.map)
        self.control_layer = folium.LayerControl()
        self.control_layer.add_to(self.map)
        self.draw_bbox(BBox.get_bbox_by_radius(self.center, self.radius))

    async def get_aircrafts_geojson(self):
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
