import pytest
import aiohttp
from unittest.mock import AsyncMock, Mock, patch

from local_flight_map.api.hexdb import (
    HexDbClient,
    HexDbConfig,
    AircraftInformation,
    AirportInformation,
    RouteInformation
)


@pytest.fixture
async def hexdb_client():
    with patch('async_lru._LRUCacheWrapper.cache_close') as close:
        close.return_value = AsyncMock()
        client = HexDbClient(HexDbConfig())
        yield client
        await client.close()


class TestHexDbClient:
    @pytest.mark.asyncio
    async def test_get_aircraft_information(self, hexdb_client):
        # Mock response data
        mock_data = {
            "ICAOTypeCode": "B738",
            "Manufacturer": "BOEING",
            "ModeS": "A83547",
            "OperatorFlagCode": "US",
            "RegisteredOwners": "SOUTHWEST AIRLINES",
            "Registration": "N12345",
            "Type": "737-800"
        }

        # Mock the session's get method
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_data)
        mock_raise_for_status = Mock(return_value=None)
        mock_response.raise_for_status = mock_raise_for_status
        mock_response.content_type = "application/json"

        with patch.object(hexdb_client, '_session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.close = AsyncMock()

            async with hexdb_client:
                # Test the method
                result = await hexdb_client.get_aircraft_information_from_hexdb("A83547")

                # Verify the result
                assert isinstance(result, AircraftInformation)
                assert result.ICAOTypeCode == "B738"
                assert result.Manufacturer == "BOEING"
                assert result.ModeS == "A83547"
                assert result.OperatorFlagCode == "US"
                assert result.RegisteredOwners == "SOUTHWEST AIRLINES"
                assert result.Registration == "N12345"
                assert result.Type == "737-800"

                # Verify the API call
                mock_session.get.assert_called_once_with(
                    "/api/v1/aircraft/a83547"
                )

    @pytest.mark.asyncio
    async def test_get_airport_information(self, hexdb_client):
        # Mock response data
        mock_data = {
            "airport": "KJFK",
            "country_code": "US",
            "iata": "JFK",
            "icao": "KJFK",
            "latitude": 40.6413,
            "longitude": -73.7781,
            "region_name": "New York"
        }

        # Mock the session's get method
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_data)
        mock_raise_for_status = Mock(return_value=None)
        mock_response.raise_for_status = mock_raise_for_status
        mock_response.content_type = "application/json"

        with patch.object(hexdb_client, '_session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.close = AsyncMock()
            async with hexdb_client:
                # Test the method
                result = await hexdb_client.get_airport_information_from_hexdb("KJFK")

                # Verify the result
                assert isinstance(result, AirportInformation)
                assert result.airport == "KJFK"
                assert result.country_code == "US"
                assert result.iata == "JFK"
                assert result.icao == "KJFK"
                assert result.latitude == 40.6413
                assert result.longitude == -73.7781
                assert result.region_name == "New York"

                # Verify the API call
                mock_session.get.assert_called_once_with(
                    "/api/v1/airport/icao/kjfk"
                )

    @pytest.mark.asyncio
    async def test_get_route_information(self, hexdb_client):
        # Mock response data
        mock_data = {
            "flight": "SWA123",
            "route": "KJFK-KLAX",
            "updatetime": 1678901234
        }

        # Mock the session's get method
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_data)
        mock_raise_for_status = Mock(return_value=None)
        mock_response.raise_for_status = mock_raise_for_status
        mock_response.content_type = "application/json"

        with patch.object(hexdb_client, '_session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.close = AsyncMock()

            async with hexdb_client:
                # Test the method
                result = await hexdb_client.get_route_information_from_hexdb("SWA123")

                # Verify the result
                assert isinstance(result, RouteInformation)
                assert result.flight == "SWA123"
                assert result.route == "KJFK-KLAX"
                assert result.updatetime == 1678901234

                # Verify the API call
                mock_session.get.assert_called_once_with(
                    "/api/v1/route/icao/swa123"
                )

    @pytest.mark.asyncio
    async def test_get_aircraft_information_not_found(self, hexdb_client):
        # Mock the session's get method to return 404
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_raise_for_status = Mock(return_value=None)
        mock_response.raise_for_status = mock_raise_for_status
        mock_response.content_type = "application/json"

        with patch.object(hexdb_client, '_session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.close = AsyncMock()

            async with hexdb_client:
                # Test the method
                result = await hexdb_client.get_aircraft_information_from_hexdb("INVALID")

                # Verify the result is None
                assert result is None

    @pytest.mark.asyncio
    async def test_get_airport_information_not_found(self, hexdb_client):
        # Mock the session's get method to return 404
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_raise_for_status = Mock(return_value=None)
        mock_response.raise_for_status = mock_raise_for_status
        mock_response.content_type = "application/json"

        with patch.object(hexdb_client, '_session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.close = AsyncMock()
            async with hexdb_client:
                # Test the method
                result = await hexdb_client.get_airport_information_from_hexdb("INVALID")

                # Verify the result is None
                assert result is None

    @pytest.mark.asyncio
    async def test_get_route_information_not_found(self, hexdb_client):
        # Mock the session's get method to return 404
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_raise_for_status = Mock(return_value=None)
        mock_response.raise_for_status = mock_raise_for_status
        mock_response.content_type = "application/json"

        with patch.object(hexdb_client, '_session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.close = AsyncMock()

            async with hexdb_client:
                # Test the method
                result = await hexdb_client.get_route_information_from_hexdb("INVALID")

                # Verify the result is None
                assert result is None

    @pytest.mark.asyncio
    async def test_get_aircraft_information_error(self, hexdb_client):
        # Mock the session's get method to raise an error
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_raise_for_status = Mock(side_effect=aiohttp.ClientResponseError(
            request_info=Mock(real_url="https://api.hexdb.com/aircraft/icao/a83547"),
            history=None,
            status=500,
            message="Server Error"
        ))
        mock_response.raise_for_status = mock_raise_for_status
        mock_response.content_type = "application/json"

        with patch.object(hexdb_client, '_session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.close = AsyncMock()

            async with hexdb_client:
                # Test the method raises the error
                with pytest.raises(aiohttp.ClientResponseError) as exc_info:
                    await hexdb_client.get_aircraft_information_from_hexdb("A83547")
                assert exc_info.value.status == 500
                assert str(exc_info.value) == (
                    "500, message='Server Error', "
                    "url='https://api.hexdb.com/aircraft/icao/a83547'"
                )
