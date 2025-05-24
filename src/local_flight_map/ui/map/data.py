from typing import Dict, Any, Union
import asyncio

from ...api import ApiClient
from ...api.adsbexchange import AdsbExchangeResponse
from ...api.opensky import States
from .config import MapConfig


class DataSource:
    """Handles aircraft data processing and enrichment"""

    def __init__(self, client: ApiClient, batch_size: int = 50):
        self._client = client
        self._batch_size = batch_size
        self._semaphore = asyncio.Semaphore(10)

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

    async def _process_feature(self, feature: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single feature with rate limiting"""
        async with self._semaphore:
            icao24 = feature["properties"]["icao24_code"]
            for result in await asyncio.gather(
                self._client.get_aircraft_information_from_hexdb(icao24),
                self._client.get_route_information_from_hexdb(icao24)
            ):
                if result:
                    feature["properties"] = result.patch_geojson_properties(feature["properties"])

            feature["properties"]["tags"] = self._generate_tags(feature["properties"])
            return feature

    async def get_aircrafts_geojson(self, config: MapConfig) -> Dict[str, Any]:
        """
        Get aircraft data in GeoJSON format.

        Args:
            center: The center of the map.
            radius: The radius of the map.

        Returns:
            The aircraft data in GeoJSON format.
        """
        if config.provider == 'adsbexchange':
            args = (config.center, config.radius)
            method = self._client.get_aircraft_from_adsbexchange_within_range
        elif config.provider == 'opensky':
            args = (config.bbox, )
            method = self._client.get_states_from_opensky
        else:
            raise ValueError(f"Invalid provider: {config.provider}")

        aircrafts: Union[AdsbExchangeResponse, States] = await method(*args)
        feature_collection: Dict[str, Any] = aircrafts.to_geojson()
        feature_collection["features"] = [
            feature for i in range(0, len(feature_collection["features"]), self._batch_size)
            for feature in await asyncio.gather(*[
                self._process_feature(feature) for feature in feature_collection["features"][i:i+self._batch_size]
            ])
        ]
        return feature_collection
