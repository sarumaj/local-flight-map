"""
Main entry point for the Local Flight Map application.
This module initializes and runs the API client and map interface.
"""

import asyncio

from .api import ApiClient, ApiConfig
from .ui import MapInterface, MapConfig


async def amain():
    """
    Asynchronous main function that initializes and runs the application.
    Creates and manages the API client and map interface instances.
    """
    api_config = ApiConfig()
    map_config = MapConfig()
    async with (
        ApiClient(api_config) as client,
        MapInterface(
            config=map_config,
            client=client
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
