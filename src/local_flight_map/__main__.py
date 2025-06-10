"""
Main entry point for the Local Flight Map application.
This module initializes and runs the API client and map interface.
"""

import asyncio

from .api import (
    AdsbExchangeClient,
    HexDbClient,
    OpenSkyClient,
    ApiConfig,
    ApiClients,
)
from .api.adsbexchange.feed import AdsbExchangeFeederClient
from .ui import MapInterface, MapConfig


async def amain():
    """
    Asynchronous main function that initializes and runs the application.
    Creates and manages the API client and map interface instances.
    """
    api_config = ApiConfig()
    map_config = MapConfig()
    async with (
        AdsbExchangeClient(api_config) as adsbexchange_client,
        HexDbClient(api_config) as hexdb_client,
        OpenSkyClient(api_config) as opensky_client,
        AdsbExchangeFeederClient(api_config) as adsbexchange_feed_client,
        MapInterface(
            config=map_config,
            clients=ApiClients(
                adsbexchange_client=adsbexchange_client,
                hexdb_client=hexdb_client,
                opensky_client=opensky_client,
                adsbexchange_feed_client=adsbexchange_feed_client
            )
        ) as map_interface
    ):
        await map_interface.serve()


def main():
    """
    Synchronous main function that runs the asynchronous main function.
    Uses asyncio to handle the asynchronous execution.
    """
    asyncio.run(amain())


if __name__ == "__main__":
    main()
