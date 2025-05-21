import asyncio
from .client import OpenSkyApi
from .config import OpenSkyConfig

async def main():
    config = OpenSkyConfig()
    print(config.model_dump())
    async with OpenSkyApi(config=config) as client:
        states = await client.get_states()
        print(states.states[0], end="\n\n")

        #my_states = await client.get_my_states()
        #print(my_states, end="\n\n")

        track = await client.get_track_by_aircraft(states.states[0].icao24)
        print(track, end="\n\n")

        flights = await client.get_flights_by_aircraft(states.states[0].icao24, begin=states.states[0].time_position, end=states.states[0].time_position + 1000)
        print(flights, end="\n\n")

if __name__ == "__main__":
    asyncio.run(main())
