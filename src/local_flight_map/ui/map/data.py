from typing import Dict, Any
from ...api.base import Location
from ...api import ApiClient


class MapData:
    """Handles aircraft data processing and enrichment"""

    def __init__(self, client: ApiClient):
        self._client = client

    def _generate_tags(self, props: Dict[str, Any]) -> list[str]:
        """
        Generate tags for aircraft properties.

        Args:
            props: The properties of the aircraft.

        Returns:
            The list of tags.
        """
        tags = []
        tags.append(f"icao24:{props.get('icao24_code')}")

        optional_tags = {
            'type': props.get('type'),
            'callsign': props.get('callsign'),
            'registration': props.get('registration'),
            'altitude': props.get('baro_altitude') or props.get('geom_altitude'),
            'speed': props.get('ground_speed'),
            'emergency': props.get('emergency_status'),
            'category': props.get('category'),
        }

        for key, value in optional_tags.items():
            if value:
                match key:
                    case 'altitude':
                        try:
                            numerical_value = float(value)
                        except ValueError:
                            tags.append("altitude:unknown")
                            continue

                        if value == 'ground' or numerical_value < 10000:
                            tags.append('altitude:low')
                        elif numerical_value < 30000:
                            tags.append('altitude:medium')
                        else:
                            tags.append('altitude:high')

                    case 'speed':
                        try:
                            numerical_value = float(value)
                        except ValueError:
                            tags.append("speed:unknown")
                            continue

                        if numerical_value < 200:
                            tags.append('speed:slow')
                        elif numerical_value < 500:
                            tags.append('speed:medium')
                        else:
                            tags.append('speed:fast')

                    case _:
                        tags.append(f"{key}:{value}")

        return tags

    async def get_aircrafts_geojson(self, center: Location, radius: float) -> Dict[str, Any]:
        """
        Get aircraft data in GeoJSON format.

        Args:
            center: The center of the map.
            radius: The radius of the map.

        Returns:
            The aircraft data in GeoJSON format.
        """
        states = await self._client.get_aircraft_from_adsbexchange_within_range(
            center, radius
        )
        states_geojson = states.to_geojson()

        for index, state_geojson in enumerate(states_geojson["features"]):
            icao24 = state_geojson["properties"]["icao24_code"]

            # Get additional aircraft information
            if (aircraft_info := await self._client.get_aircraft_information_from_hexdb(icao24)) is not None:
                state_geojson["properties"] = aircraft_info.patch_geojson_properties(state_geojson["properties"])

            # Get route information
            if (route_info := await self._client.get_route_information_from_hexdb(icao24)) is not None:
                state_geojson["properties"] = route_info.patch_geojson_properties(state_geojson["properties"])

            # Add tags
            state_geojson["properties"]["tags"] = self._generate_tags(state_geojson["properties"])
            states_geojson["features"][index] = state_geojson

        return states_geojson
