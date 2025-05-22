import asyncio
from . import ApiClient, ApiConfig, Location


async def main():
    config = ApiConfig()
    print(config.model_dump(), end="\n\n")

    async with ApiClient(config=config) as client:
        response = await client.get_aircraft_from_adsbexchange_within_range(
            Location(latitude=40.6413, longitude=-73.7781),
            100
        )

        print(response)

if __name__ == "__main__":
    asyncio.run(main())
