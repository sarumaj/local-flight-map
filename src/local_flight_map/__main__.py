import asyncio
import argparse

from .api import ApiClient, ApiConfig, Location
from .ui import MapInterface, MapConfig


async def amain(args: argparse.Namespace):
    config = ApiConfig()
    async with (
        ApiClient(config) as client,
        MapInterface(
            config=MapConfig(
                center=Location(args.latitude, args.longitude),
                radius=args.radius,
                dev_mode=args.dev,
                port=args.port,
                provider=args.provider
            ),
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
    parser.add_argument(
        "--latitude",
        type=float,
        default=50.15,
        help="The latitude of the center of the map"
    )
    parser.add_argument(
        "--longitude",
        type=float,
        default=8.3166667,
        help="The longitude of the center of the map"
    )
    parser.add_argument(
        "--radius",
        type=float,
        default=50,
        help="The radius of the map in kilometers"
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Run in development mode"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5006,
        help="The port to run the server on"
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="adsbexchange",
        choices=["adsbexchange", "opensky"],
        help="The provider to use for the map"
    )
    args = parser.parse_args()
    asyncio.run(amain(args))
