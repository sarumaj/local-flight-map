import asyncio
import argparse

from ..api.base import Location
from ..api import ApiClient, ApiConfig
from .map.interface import MapInterface


async def amain(args: argparse.Namespace):
    config = ApiConfig()
    async with (
        ApiClient(config) as client,
        MapInterface(
            center=Location(args.latitude, args.longitude),
            radius=args.radius,
            client=client
        ) as map_interface
    ):
        await map_interface.serve()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="local-flight-map",
        description="Run the local flight map UI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--latitude", type=float, default=50.15)
    parser.add_argument("--longitude", type=float, default=8.3166667)
    parser.add_argument("--radius", type=float, default=50)
    args = parser.parse_args()
    asyncio.run(amain(args))
