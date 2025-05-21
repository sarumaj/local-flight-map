import asyncio
from .client import ApiClient
from .config import ApiConfig


async def main():
    config = ApiConfig()
    print(config.model_dump(), end="\n\n")

    async with ApiClient(config=config) as client:
        states = await client.get_states()
        print(states.states[0], end="\n\n")

        # my_states = await client.get_my_states()
        # print(my_states, end="\n\n")

        track = await client.get_track_by_aircraft(states.states[0].icao24.strip())
        print(track, end="\n\n")

        route = await client.get_route_information(states.states[0].callsign.strip())
        print(route, end="\n\n")

        origin, destination = route.route.strip().rsplit("-", 1)

        origin_airport = await client.get_airport_information(origin)
        print(origin_airport, end="\n\n")

        destination_airport = await client.get_airport_information(destination)
        print(destination_airport, end="\n\n")

        aircraft = await client.get_aircraft_information(states.states[0].icao24.strip())
        print(aircraft, end="\n\n")

if __name__ == "__main__":
    asyncio.run(main())
