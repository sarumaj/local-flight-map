import asyncio

from .api import ApiClient, ApiConfig
from .ui import MapInterface, MapConfig


async def amain():
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
    asyncio.run(amain())


if __name__ == "__main__":
    main()
