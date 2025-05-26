"""
Data source module for the Local Flight Map application.
Handles aircraft data processing, enrichment, and conversion to GeoJSON format.
"""

from typing import Dict, Any, Union
import asyncio

from ...api import ApiClient, Location
from ...api.adsbexchange import AdsbExchangeResponse
from ...api.opensky import States
from .config import MapConfig, logger


class DataSource:
    """
    Handles aircraft data processing and enrichment.
    Manages data retrieval from different providers and enriches it with additional information.
    """

    def __init__(self, client: ApiClient, config: MapConfig):
        """
        Initialize the data source.

        Args:
            client: The API client for fetching aircraft data.
            config: The map configuration containing data source settings.
        """
        self._client = client
        self._config = config
        self._hexdb_semaphore = asyncio.Semaphore(5)  # Limit concurrent HexDB API calls

    def _generate_tags(self, props: Dict[str, Any]) -> list[str]:
        """
        Generate tags for aircraft properties based on their characteristics.

        Args:
            props: The properties of the aircraft.

        Returns:
            A list of tags describing the aircraft's characteristics.
            Tags are generated for:
            - ICAO24 code
            - Aircraft type
            - Callsign
            - Registration
            - Altitude (low/medium/high)
            - Speed (slow/medium/fast)
            - Emergency status
            - Category
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
        """
        Process a single aircraft feature with rate limiting.
        Enriches the feature with additional information from HexDB.

        Args:
            feature: The aircraft feature to process.

        Returns:
            The enriched aircraft feature.
        """
        if not hasattr(self, "_semaphore"):
            self._semaphore = asyncio.Semaphore(self._config.data_max_threads)

        async with self._semaphore:
            try:
                icao24 = feature["properties"]["icao24_code"]
                async with self._hexdb_semaphore:
                    for result in await asyncio.gather(
                        self._client.get_aircraft_information_from_hexdb(icao24),
                        self._client.get_route_information_from_hexdb(icao24),
                        return_exceptions=True
                    ):
                        if isinstance(result, Exception):
                            logger.error(f"Error processing feature {icao24}: {str(result)}")
                            continue
                        if result:
                            feature["properties"] = result.patch_geojson_properties(feature["properties"])

                feature["properties"]["tags"] = self._generate_tags(feature["properties"])

            except Exception as e:
                icao24 = feature.get('properties', {}).get('icao24_code', 'unknown')
                logger.error(f"Error processing feature {icao24}: {str(e)}")

            finally:
                return feature

    async def get_aircrafts_geojson(self) -> Dict[str, Any]:
        """
        Get aircraft data in GeoJSON format.
        Retrieves data from the configured provider and processes it in batches.

        Returns:
            A GeoJSON feature collection containing the processed aircraft data.
            Returns None if no data is available.

        Raises:
            ValueError: If the configured data provider is invalid.
        """
        match self._config.data_provider:
            case 'adsbexchange':
                args = (self._config.map_center, self._config.map_radius)
                method = self._client.get_aircraft_from_adsbexchange_within_range
            case 'opensky':
                args = (0, None, self._config.map_bbox)
                method = self._client.get_states_from_opensky
            case _:
                raise ValueError(f"Invalid provider: {self._config.data_provider}")

        aircrafts: Union[AdsbExchangeResponse, States, None] = await method(*args)
        if aircrafts is None:
            logger.error(f"No aircrafts found for {self._config.map_center} and {self._config.map_radius} ({self._config.map_bbox})")
            return None

        feature_collection: Dict[str, Any] = aircrafts.to_geojson()
        feature_collection["features"] = [
            feature for i in range(0, len(feature_collection["features"]), self._config.data_batch_size)
            for feature in await asyncio.gather(*[
                self._process_feature(feature)
                for feature in feature_collection["features"][i:i+self._config.data_batch_size]
            ])
        ]
        feature_collection["features"] = sorted(
            feature_collection["features"], 
            key=lambda x: Location(x["geometry"]["coordinates"][1], x["geometry"]["coordinates"][0]).get_angle_to(self._config.map_center),
        )
        return feature_collection
