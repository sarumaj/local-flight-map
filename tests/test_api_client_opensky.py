import pytest
import aiohttp
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from local_flight_map.api.opensky import (
    OpenSkyClient,
    OpenSkyConfig,
    States,
    StateVector,
    FlightTrack,
    Waypoint,
)
from local_flight_map.api.base import BBox


@pytest.fixture
async def opensky_client():
    config = OpenSkyConfig(
        opensky_client_id="",
        opensky_client_secret=""
    )
    with patch('async_lru._LRUCacheWrapper.cache_close') as close:
        close.return_value = AsyncMock()
        client = OpenSkyClient(config)
        yield client
        await client.close()


@pytest.fixture
async def authenticated_opensky_client():
    config = OpenSkyConfig(
        opensky_client_id="test_id",
        opensky_client_secret="test_secret"
    )
    with patch('async_lru._LRUCacheWrapper.cache_close') as close:
        close.return_value = AsyncMock()
        client = OpenSkyClient(config)
        yield client
        await client.close()


class TestOpenSkyClient:
    @pytest.mark.asyncio
    async def test_get_states_from_opensky(self, opensky_client):
        # Mock response data
        mock_data = {
            "time": 1678901234,
            "states": [
                [
                    "a83547",  # icao24
                    "SWA123",  # callsign
                    "United States",  # origin_country
                    1678901234,  # time_position
                    1678901234,  # last_contact
                    40.6413,  # longitude
                    -73.7781,  # latitude
                    35000.0,  # baro_altitude
                    False,  # on_ground
                    250.0,  # velocity
                    90.0,  # true_track
                    0.0,  # vertical_rate
                    [1, 2],  # sensors
                    35000.0,  # geo_altitude
                    "1234",  # squawk
                    False,  # spi
                    0,  # position_source
                    3  # category
                ]
            ]
        }

        # Mock the session's get method
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_data)
        mock_raise_for_status = Mock(return_value=None)
        mock_response.raise_for_status = mock_raise_for_status
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.content_type = "application/json"

        with patch.object(opensky_client, '_session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.close = AsyncMock()

            async with opensky_client:
                # Test the method
                result = await opensky_client.get_states_from_opensky()

                # Verify the result
                assert isinstance(result, States)
                assert result.time == 1678901234
                assert len(result.states) == 1
                state = result.states[0]
                assert isinstance(state, StateVector)
                assert state.icao24 == "a83547"
                assert state.callsign == "SWA123"
                assert state.origin_country == "United States"
                assert state.time_position == 1678901234
                assert state.last_contact == 1678901234
                assert state.longitude == 40.6413
                assert state.latitude == -73.7781
                assert state.baro_altitude == 35000.0
                assert not state.on_ground
                assert state.velocity == 250.0
                assert state.true_track == 90.0
                assert state.vertical_rate == 0.0
                assert state.sensors == [1, 2]
                assert state.geo_altitude == 35000.0
                assert state.squawk == "1234"
                assert not state.spi
                assert state.position_source == 0
                assert state.category == 3

                # Verify the API call
                mock_session.get.assert_called_once_with(
                    "/api/states/all",
                    params={'extended': 1}
                )

    @pytest.mark.asyncio
    async def test_get_states_from_opensky_with_params(self, opensky_client):
        # Mock response data
        mock_data = {
            "time": 1678901234,
            "states": []
        }

        # Mock the session's get method
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_data)
        mock_raise_for_status = Mock(return_value=None)
        mock_response.raise_for_status = mock_raise_for_status
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.content_type = "application/json"

        with patch.object(opensky_client, '_session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.close = AsyncMock()

            async with opensky_client:
                # Test with various parameters
                time = datetime(2023, 3, 15, 12, 0)
                icao24 = ("a83547", "b12345")
                bbox = BBox(min_lat=40.0, max_lat=41.0, min_lon=-74.0, max_lon=-73.0)

                await opensky_client.get_states_from_opensky(
                    time_secs=time,
                    icao24=icao24,
                    bbox=bbox
                )

                # Verify the API call parameters
                mock_session.get.assert_called_once_with(
                    "/api/states/all",
                    params={
                        'extended': 1,
                        'time': int(time.timestamp()),
                        'icao24': 'a83547,b12345',
                        'lamax': 41.0,
                        'lomax': -73.0,
                        'lomin': -74.0,
                        'lamin': 40.0
                    }
                )

    @pytest.mark.asyncio
    async def test_get_my_states_from_opensky(self, authenticated_opensky_client):
        # Mock response data
        mock_data = {
            "time": 1678901234,
            "states": []
        }

        # Mock the session's get method
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_data)
        mock_raise_for_status = Mock(return_value=None)
        mock_response.raise_for_status = mock_raise_for_status
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.content_type = "application/json"

        with patch.object(authenticated_opensky_client, '_session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.close = AsyncMock()

            async with authenticated_opensky_client:
                # Test the method
                result = await authenticated_opensky_client.get_my_states_from_opensky()

                # Verify the result
                assert isinstance(result, States)
                assert result.time == 1678901234
                assert len(result.states) == 0

                # Verify the API call
                mock_session.get.assert_called_once_with(
                    "/api/states/own",
                    params={'extended': 1}
                )

    @pytest.mark.asyncio
    async def test_get_my_states_from_opensky_requires_auth(self, opensky_client):
        async with opensky_client:
            # Test that unauthenticated client raises error
            with pytest.raises(ValueError, match="OAuth2 client credentials required for this operation"):
                await opensky_client.get_my_states_from_opensky()

    @pytest.mark.asyncio
    async def test_get_track_by_aircraft_from_opensky(self, opensky_client):
        # Mock response data
        mock_data = {
            "icao24": "a83547",
            "startTime": 1678901234,
            "endTime": 1678902234,
            "callsign": "SWA123",
            "path": [
                {
                    "time": 1678901234,
                    "latitude": 40.6413,
                    "longitude": -73.7781,
                    "baro_altitude": 35000.0,
                    "true_track": 90.0,
                    "on_ground": False
                }
            ]
        }

        # Mock the session's get method
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_data)
        mock_raise_for_status = Mock(return_value=None)
        mock_response.raise_for_status = mock_raise_for_status
        mock_response.content_type = "application/json"

        with patch.object(opensky_client, '_session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.close = AsyncMock()

            async with opensky_client:
                # Test the method
                result = await opensky_client.get_track_by_aircraft_from_opensky("a83547")

                # Verify the result
                assert isinstance(result, FlightTrack)
                assert result.icao24 == "a83547"
                assert result.startTime == 1678901234
                assert result.endTime == 1678902234
                assert result.callsign == "SWA123"
                assert len(result.path) == 1
                waypoint = result.path[0]
                assert isinstance(waypoint, Waypoint)
                assert waypoint.time == 1678901234
                assert waypoint.latitude == 40.6413
                assert waypoint.longitude == -73.7781
                assert waypoint.baro_altitude == 35000.0
                assert waypoint.true_track == 90.0
                assert not waypoint.on_ground

                # Verify the API call
                mock_session.get.assert_called_once_with(
                    "/api/tracks/all",
                    params={
                        'icao24': 'a83547',
                        'time': 0
                    }
                )

    @pytest.mark.asyncio
    async def test_get_track_by_aircraft_from_opensky_old_data(self, opensky_client):
        async with opensky_client:
            # Test that requesting data older than 30 days raises error
            old_time = int(datetime.now().timestamp()) - (31 * 24 * 60 * 60)  # 31 days ago
            with pytest.raises(
                ValueError,
                match="It is not possible to access flight tracks from more than 30 days in the past"
            ):
                await opensky_client.get_track_by_aircraft_from_opensky("a83547", time_secs=old_time)

    @pytest.mark.asyncio
    async def test_get_states_from_opensky_invalid_bbox(self, opensky_client):
        async with opensky_client:
            # Test that invalid bounding box values raise error
            with pytest.raises(ValueError, match="Invalid latitude value: 91.0"):
                await opensky_client.get_states_from_opensky(
                    bbox=BBox(min_lat=91.0, max_lat=92.0, min_lon=-180.0, max_lon=180.0)
                )

    @pytest.mark.asyncio
    async def test_get_states_from_opensky_error(self, opensky_client):
        # Mock the session's get method to raise an error
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_raise_for_status = Mock(side_effect=aiohttp.ClientResponseError(
            request_info=Mock(real_url="https://opensky-network.org/api/states/all"),
            history=None,
            status=500,
            message="Server Error"
        ))
        mock_response.raise_for_status = mock_raise_for_status
        mock_response.content_type = "application/json"

        with patch.object(opensky_client, '_session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.close = AsyncMock()

            async with opensky_client:
                # Test the method raises the error
                with pytest.raises(aiohttp.ClientResponseError) as exc_info:
                    await opensky_client.get_states_from_opensky()
                assert exc_info.value.status == 500
                assert str(exc_info.value) == (
                    "500, message='Server Error', "
                    "url='https://opensky-network.org/api/states/all'"
                )
