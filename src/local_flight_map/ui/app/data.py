"""
Data source module for the Local Flight Map application.
Handles aircraft data processing, enrichment, and conversion to GeoJSON format.
"""

from typing import Dict, Any, Union, Tuple, Optional
import asyncio

from ...api import ApiClients, Location
from ...api.adsbexchange import AdsbExchangeResponse
from ...api.opensky import States
from .config import MapConfig, logger


class DataSource:
    """
    Handles aircraft data processing and enrichment.
    Manages data retrieval from different providers and enriches it with additional information.
    """

    def __init__(
        self,
        clients: ApiClients,
        config: MapConfig
    ):
        """
        Initialize the data source.

        Args:
            clients: The API clients for fetching aircraft data from ADSBExchange, HexDB, and OpenSky.
            config: The map configuration containing data source settings.
        """
        self._clients = clients
        self._config = config
        self._hexdb_semaphore = asyncio.Semaphore(5)  # Limit concurrent HexDB API calls

    def _generate_tags(self, feature: Dict[str, Any], inplace: bool = False) -> list[str]:
        """
        Generate tags for aircraft properties based on their characteristics.

        Args:
            feature: The aircraft feature to generate tags for.
            inplace: Whether to update the feature in place.

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
        properties = feature.get('properties', {}).copy()

        tags = []
        tags.append(f"icao24:{properties.get('icao24_code')}")

        optional_tags = {
            'type': properties.get('type'),
            'callsign': properties.get('callsign'),
            'registration': properties.get('registration'),
            'altitude': properties.get('baro_altitude') or properties.get('geom_altitude'),
            'speed': properties.get('ground_speed'),
            'emergency': properties.get('emergency_status'),
            'category': properties.get('category'),
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

        properties["tags"] = tags
        if inplace:
            feature["properties"] = properties
            return feature

        return {
            "type": feature["type"],
            "geometry": feature["geometry"],
            "properties": properties
        }

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
                icao24 = feature.get("properties", {}).get("icao24_code", "unknown")
                callsign = feature.get("properties", {}).get("callsign", "unknown")
                async with self._hexdb_semaphore:
                    for result in await asyncio.gather(
                        self._clients.hexdb_client.get_aircraft_information_from_hexdb(icao24),
                        self._clients.hexdb_client.get_route_information_from_hexdb(callsign),
                        return_exceptions=True
                    ):
                        if isinstance(result, Exception):
                            logger.error(f"Error processing feature {icao24}: {str(result)}")
                            continue
                        if result:
                            result.enrich_geojson(feature, inplace=True)

                    async def resolve_route(label: str, route: str) -> Tuple[str, Optional[Dict[str, Any]]]:
                        airport = await self._clients.hexdb_client.get_airport_information_from_hexdb(route)
                        return label, airport.to_geojson() if airport else None

                    for label, airport in await asyncio.gather(
                        *[
                            resolve_route(label, route)
                            for label, route in zip(
                                ("origin", "destination"),
                                feature.get("properties", {}).get("route", "-").split("-", 1)
                            )
                            if route
                        ]
                    ):
                        for name, value in airport["properties"].items():
                            feature["properties"][f"{label}_{name}"] = value

                self._generate_tags(feature, inplace=True)

            except Exception as e:
                logger.error(f"Error processing feature {icao24}/{callsign}: {str(e)}")

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
                method = self._clients.adsbexchange_client.get_aircraft_from_adsbexchange_within_range
            case 'opensky':
                args = (0, None, self._config.map_bbox)
                method = self._clients.opensky_client.get_states_from_opensky
            case _:
                raise ValueError(f"Invalid provider: {self._config.data_provider}")

        aircrafts: Union[AdsbExchangeResponse, States, None] = await method(*args)
        if aircrafts is None:
            logger.error(
                f"No aircrafts found for {self._config.map_center} and {self._config.map_radius} "
                f"({self._config.map_bbox})"
            )
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
            key=lambda x: Location(
                x["geometry"]["coordinates"][1],
                x["geometry"]["coordinates"][0]
            ).get_angle_to(self._config.map_center),
        )
        return feature_collection
