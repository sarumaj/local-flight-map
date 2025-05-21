import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
import aiohttp

from local_flight_map.open_sky_api.client import OpenSkyApi
from local_flight_map.open_sky_api.config import OpenSkyConfig
from local_flight_map.open_sky_api.response_objects import OpenSkyStates, FlightTrack


@pytest.fixture
def mock_response():
    mock = AsyncMock()
    mock.status = 200
    mock.__aenter__.return_value = mock
    mock.__aexit__.return_value = None
    mock.json = AsyncMock()
    return mock


@pytest.fixture
async def api_client():
    config = OpenSkyConfig(opensky_username="test",
                            opensky_password="test")
    async with OpenSkyApi(config=config) as client:
        yield client


@pytest.mark.asyncio
async def test_get_states_success(api_client, mock_response):
    # Mock response data
    mock_data = {
        'time': 1234567890,
        'states': [
            [
                'abc123',  # icao24
                'TEST123',  # callsign
                'United States',  # origin_country
                1234567890,  # time_position
                1234567890,  # last_contact
                45.0,  # longitude
                30.0,  # latitude
                1000.0,  # geo_altitude
                False,  # on_ground
                500.0,  # velocity
                90.0,  # true_track
                10.0,  # vertical_rate
                [1, 2, 3],  # sensors
                1000.0,  # baro_altitude
                '1234',  # squawk
                False,  # spi
                0,  # position_source
                0  # category
            ]
        ]
    }
    mock_response.json.return_value = mock_data

    with patch('aiohttp.ClientSession.get', return_value=mock_response):
        result = await api_client.get_states()

    assert result is not None
    assert isinstance(result, OpenSkyStates)
    assert result.time == 1234567890
    assert len(result.states) == 1
    assert result.states[0].icao24 == 'abc123'
    assert result.states[0].callsign == 'TEST123'
    assert result.states[0].origin_country == 'United States'


@pytest.mark.asyncio
async def test_get_states_with_params(api_client, mock_response):
    mock_data = {
        'time': 1234567890,
        'states': []
    }
    mock_response.json.return_value = mock_data

    with patch('aiohttp.ClientSession.get', return_value=mock_response) as mock_get:
        await api_client.get_states(
            time_secs=datetime.fromtimestamp(1234567890),
            icao24=['abc123', 'def456'],
            bbox=(30.0, 40.0, -120.0, -110.0)
        )

        # Verify the request parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert 'params' in kwargs
        params = kwargs['params']
        assert params['time'] == 1234567890
        assert params['icao24'] == 'abc123,def456'
        assert params['lamin'] == 30.0
        assert params['lamax'] == 40.0
        assert params['lomin'] == -120.0
        assert params['lomax'] == -110.0


@pytest.mark.asyncio
async def test_get_states_error(api_client, mock_response):
    mock_response.status = 404
    mock_response.json.return_value = None

    with patch('aiohttp.ClientSession.get', return_value=mock_response), pytest.raises(Exception, match="Failed to get states: None"):
        result = await api_client.get_states()
        assert result is None


@pytest.mark.asyncio
async def test_get_my_states_success(api_client, mock_response):
    mock_data = {
        'time': 1234567890,
        'states': [
            [
                'abc123',  # icao24
                'TEST123',  # callsign
                'United States',  # origin_country
                1234567890,  # time_position
                1234567890,  # last_contact
                45.0,  # longitude
                30.0,  # latitude
                1000.0,  # geo_altitude
                False,  # on_ground
                500.0,  # velocity
                90.0,  # true_track
                10.0,  # vertical_rate
                [1, 2, 3],  # sensors
                1000.0,  # baro_altitude
                '1234',  # squawk
                False,  # spi
                0,  # position_source
                0  # category
            ]
        ]
    }
    mock_response.json.return_value = mock_data

    with patch('aiohttp.ClientSession.get', return_value=mock_response):
        result = await api_client.get_my_states()

    assert result is not None
    assert isinstance(result, OpenSkyStates)
    assert result.time == 1234567890
    assert len(result.states) == 1
    assert result.states[0].icao24 == 'abc123'


@pytest.mark.asyncio
async def test_get_my_states_auth_required():
    # Create a new client without credentials
    config = OpenSkyConfig()
    async with OpenSkyApi(config=config) as client:
        with pytest.raises(ValueError, match="Authentication required for this operation"):
            await client.get_my_states()


@pytest.mark.asyncio
async def test_get_track_by_aircraft_success(api_client, mock_response):
    mock_data = {
        'icao24': 'abc123',
        'startTime': 1234567890,
        'endTime': 1234567899,
        'callsign': 'TEST123',
        'path': [
            [1234567890, 30.0, 45.0, 1000.0, 90.0, False],
            [1234567891, 31.0, 46.0, 2000.0, 91.0, False]
        ]
    }
    mock_response.json.return_value = mock_data

    with patch('aiohttp.ClientSession.get', return_value=mock_response):
        result = await api_client.get_track_by_aircraft(
            icao24='abc123',
            time=datetime.fromtimestamp(1234567890)
        )

    assert result is not None
    assert isinstance(result, FlightTrack)
    assert result.icao24 == 'abc123'
    assert result.callsign == 'TEST123'
    assert len(result.path) == 2
    assert result.path[0].latitude == 30.0
    assert result.path[1].latitude == 31.0


@pytest.mark.asyncio
async def test_get_track_by_aircraft_error(api_client, mock_response):
    mock_response.status = 404
    mock_response.json.return_value = None

    with patch('aiohttp.ClientSession.get', return_value=mock_response), pytest.raises(Exception, match="No data returned"):
        result = await api_client.get_track_by_aircraft(
            icao24='abc123',
            time=datetime.fromtimestamp(1234567890)
        )
        assert result is None


@pytest.mark.asyncio
async def test_context_manager():
    config = OpenSkyConfig(username="test", password="test")
    async with OpenSkyApi(config=config) as client:
        assert client._session is not None
        assert isinstance(client._session, aiohttp.ClientSession)
    
    # Session should be closed after context manager exits
    assert client._session is None 