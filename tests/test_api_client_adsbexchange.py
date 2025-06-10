import pytest
import aiohttp
from unittest.mock import AsyncMock, Mock, patch
from local_flight_map.api.adsbexchange import (
    AdsbExchangeClient,
    AdsbExchangeConfig,
    AdsbExchangeResponse,
    AircraftProperties,
)
from local_flight_map.api.base import Location


@pytest.fixture
async def adsbexchange_client():
    config = AdsbExchangeConfig(
        adsbexchange_api_key="test_key"
    )
    with patch('async_lru._LRUCacheWrapper.cache_close') as close:
        close.return_value = AsyncMock()
        client = AdsbExchangeClient(config)
        yield client
        await client.close()


def get_mock_aircraft_data():
    """Helper function to get complete mock aircraft data"""
    return {
        "hex": "a83547",
        "type": "adsb_icao",
        "flight": "SWA123",
        "r": "N12345",
        "t": "B738",
        "dbFlags": 0,
        "alt_baro": 35000,
        "alt_geom": 35000,
        "gs": 250.0,
        "ias": 240.0,
        "tas": 245.0,
        "mach": 0.78,
        "wd": 270.0,
        "ws": 50.0,
        "oat": -50.0,
        "tat": -45.0,
        "track": 90.0,
        "track_rate": 0.0,
        "roll": 0.0,
        "mag_heading": 90.0,
        "true_heading": 90.0,
        "baro_rate": 0.0,
        "geom_rate": 0.0,
        "squawk": "1234",
        "emergency": "none",
        "category": "A3",
        "nav_qnh": 1013.2,
        "nav_altitude_mcp": 35000,
        "nav_altitude_fms": 35000,
        "nav_heading": 90.0,
        "nav_modes": ["autopilot", "vnav"],
        "lat": 40.6413,
        "lon": -73.7781,
        "nic": 8,
        "rc": 185,
        "seen_pos": 0.0,
        "version": 2,
        "nic_baro": 1,
        "nac_p": 9,
        "nac_v": 1,
        "sil": 3,
        "sil_type": "perhour",
        "gva": 2,
        "sda": 2,
        "alert": 0,
        "spi": 0,
        "mlat": [],
        "tisb": [],
        "messages": 100,
        "seen": 0.0,
        "rssi": -20.0
    }


def get_mock_response_data():
    """Helper function to get complete mock response data"""
    return {
        "ac": [get_mock_aircraft_data()],
        "msg": "No error",
        "now": 1678901234,
        "total": 1,
        "ctime": 1678901234000,
        "ptime": 10
    }


class TestAdsbExchangeClient:
    @pytest.mark.asyncio
    async def test_get_aircraft_by_registration(self, adsbexchange_client):
        # Mock response data
        mock_data = get_mock_response_data()

        # Mock the session's get method
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_data)
        mock_response.raise_for_status = Mock(return_value=None)
        mock_response.content_type = "application/json"

        with patch.object(adsbexchange_client, '_session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.close = AsyncMock()

            async with adsbexchange_client:
                # Test the method
                result = await adsbexchange_client.get_aircraft_from_adsbexchange_by_registration("N12345")

                # Verify the result
                assert isinstance(result, AdsbExchangeResponse)
                assert result.msg == "No error"
                assert result.now == 1678901234
                assert result.total == 1
                assert result.ctime == 1678901234000
                assert result.ptime == 10

                assert len(result.ac) == 1
                aircraft = result.ac[0]
                assert isinstance(aircraft, AircraftProperties)
                assert aircraft.hex == "a83547"
                assert aircraft.type == "adsb_icao"
                assert aircraft.flight == "SWA123"
                assert aircraft.r == "N12345"
                assert aircraft.t == "B738"
                assert aircraft.alt_baro == 35000
                assert aircraft.alt_geom == 35000
                assert aircraft.gs == 250.0
                assert aircraft.ias == 240.0
                assert aircraft.tas == 245.0
                assert aircraft.mach == 0.78
                assert aircraft.wd == 270.0
                assert aircraft.ws == 50.0
                assert aircraft.oat == -50.0
                assert aircraft.tat == -45.0
                assert aircraft.track == 90.0
                assert aircraft.track_rate == 0.0
                assert aircraft.roll == 0.0
                assert aircraft.mag_heading == 90.0
                assert aircraft.true_heading == 90.0
                assert aircraft.baro_rate == 0.0
                assert aircraft.geom_rate == 0.0
                assert aircraft.squawk == "1234"
                assert aircraft.emergency == "none"
                assert aircraft.category == "A3"
                assert aircraft.nav_qnh == 1013.2
                assert aircraft.nav_altitude_mcp == 35000
                assert aircraft.nav_altitude_fms == 35000
                assert aircraft.nav_heading == 90.0
                assert aircraft.nav_modes == ["autopilot", "vnav"]
                assert aircraft.lat == 40.6413
                assert aircraft.lon == -73.7781
                assert aircraft.nic == 8
                assert aircraft.rc == 185
                assert aircraft.seen_pos == 0.0
                assert aircraft.version == 2
                assert aircraft.nic_baro == 1
                assert aircraft.nac_p == 9
                assert aircraft.nac_v == 1
                assert aircraft.sil == 3
                assert aircraft.sil_type == "perhour"
                assert aircraft.gva == 2
                assert aircraft.sda == 2
                assert aircraft.alert == 0
                assert aircraft.spi == 0
                assert aircraft.mlat == []
                assert aircraft.tisb == []
                assert aircraft.messages == 100
                assert aircraft.seen == 0.0
                assert aircraft.rssi == -20.0

                # Verify the API call
                mock_session.get.assert_called_once_with(
                    "/v2/registration/N12345"
                )

    @pytest.mark.asyncio
    async def test_get_aircraft_by_icao24(self, adsbexchange_client):
        # Mock response data
        mock_data = get_mock_response_data()

        # Mock the session's get method
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_data)
        mock_response.raise_for_status = Mock(return_value=None)
        mock_response.content_type = "application/json"

        with patch.object(adsbexchange_client, '_session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.close = AsyncMock()

            async with adsbexchange_client:
                # Test the method
                result = await adsbexchange_client.get_aircraft_from_adsbexchange_by_icao24("a83547")

                # Verify the result
                assert isinstance(result, AdsbExchangeResponse)
                assert len(result.ac) == 1
                aircraft = result.ac[0]
                assert isinstance(aircraft, AircraftProperties)
                assert aircraft.hex == "a83547"
                assert aircraft.flight == "SWA123"
                assert aircraft.r == "N12345"

                # Verify the API call
                mock_session.get.assert_called_once_with(
                    "/v2/icao/a83547"
                )

    @pytest.mark.asyncio
    async def test_get_aircraft_by_callsign(self, adsbexchange_client):
        # Mock response data
        mock_data = get_mock_response_data()

        # Mock the session's get method
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_data)
        mock_response.raise_for_status = Mock(return_value=None)
        mock_response.content_type = "application/json"

        with patch.object(adsbexchange_client, '_session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.close = AsyncMock()

            async with adsbexchange_client:
                # Test the method
                result = await adsbexchange_client.get_aircraft_from_adsbexchange_by_callsign("SWA123")

                # Verify the result
                assert isinstance(result, AdsbExchangeResponse)
                assert len(result.ac) == 1
                aircraft = result.ac[0]
                assert isinstance(aircraft, AircraftProperties)
                assert aircraft.hex == "a83547"
                assert aircraft.flight == "SWA123"
                assert aircraft.r == "N12345"

                # Verify the API call
                mock_session.get.assert_called_once_with(
                    "/v2/callsign/swa123"
                )

    @pytest.mark.asyncio
    async def test_get_aircraft_by_squawk(self, adsbexchange_client):
        # Mock response data
        mock_data = get_mock_response_data()

        # Mock the session's get method
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_data)
        mock_response.raise_for_status = Mock(return_value=None)
        mock_response.content_type = "application/json"

        with patch.object(adsbexchange_client, '_session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.close = AsyncMock()

            async with adsbexchange_client:
                # Test the method
                result = await adsbexchange_client.get_aircraft_from_adsbexchange_by_squawk("1234")

                # Verify the result
                assert isinstance(result, AdsbExchangeResponse)
                assert len(result.ac) == 1
                aircraft = result.ac[0]
                assert isinstance(aircraft, AircraftProperties)
                assert aircraft.hex == "a83547"
                assert aircraft.squawk == "1234"

                # Verify the API call
                mock_session.get.assert_called_once_with(
                    "/v2/sqk/1234"
                )

    @pytest.mark.asyncio
    async def test_get_military_aircrafts(self, adsbexchange_client):
        # Mock response data
        mock_data = get_mock_response_data()

        # Mock the session's get method
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_data)
        mock_response.raise_for_status = Mock(return_value=None)
        mock_response.content_type = "application/json"

        with patch.object(adsbexchange_client, '_session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.close = AsyncMock()

            async with adsbexchange_client:
                # Test the method
                result = await adsbexchange_client.get_military_aircrafts_from_adsbexchange()

                # Verify the result
                assert isinstance(result, AdsbExchangeResponse)
                assert len(result.ac) == 1
                aircraft = result.ac[0]
                assert isinstance(aircraft, AircraftProperties)
                assert aircraft.hex == "a83547"

                # Verify the API call
                mock_session.get.assert_called_once_with(
                    "/v2/mil"
                )

    @pytest.mark.asyncio
    async def test_get_aircraft_within_range(self, adsbexchange_client):
        # Mock response data
        mock_data = get_mock_response_data()

        # Mock the session's get method
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_data)
        mock_response.raise_for_status = Mock(return_value=None)
        mock_response.content_type = "application/json"

        with patch.object(adsbexchange_client, '_session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.close = AsyncMock()

            async with adsbexchange_client:
                # Test the method
                center = Location(latitude=40.6413, longitude=-73.7781)
                result = await adsbexchange_client.get_aircraft_from_adsbexchange_within_range(center, 100)

                # Verify the result
                assert isinstance(result, AdsbExchangeResponse)
                assert len(result.ac) == 1
                aircraft = result.ac[0]
                assert isinstance(aircraft, AircraftProperties)
                assert aircraft.hex == "a83547"

                # Verify the API call
                mock_session.get.assert_called_once_with(
                    "/v2/lat/40.641300/lon/-73.778100/dist/100.000"
                )

    @pytest.mark.asyncio
    async def test_get_aircraft_not_found(self, adsbexchange_client):
        # Mock the session's get method to return 404
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.raise_for_status = Mock(return_value=None)
        mock_response.content_type = "application/json"

        with patch.object(adsbexchange_client, '_session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.close = AsyncMock()

            async with adsbexchange_client:
                # Test the method
                result = await adsbexchange_client.get_aircraft_from_adsbexchange_by_registration("INVALID")

                # Verify the result is None
                assert result is None

    @pytest.mark.asyncio
    async def test_get_aircraft_error(self, adsbexchange_client):
        # Mock the session's get method to raise an error
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.raise_for_status = Mock(side_effect=aiohttp.ClientResponseError(
            request_info=Mock(real_url="https://adsbexchange-com1.p.rapidapi.com/v2/registration/N12345"),
            history=None,
            status=500,
            message="Server Error"
        ))
        mock_response.content_type = "application/json"

        with patch.object(adsbexchange_client, '_session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.close = AsyncMock()

            async with adsbexchange_client:
                # Test the method raises the error
                with pytest.raises(aiohttp.ClientResponseError) as exc_info:
                    await adsbexchange_client.get_aircraft_from_adsbexchange_by_registration("N12345")
                assert exc_info.value.status == 500
                assert str(exc_info.value) == (
                    "500, message='Server Error', "
                    "url='https://adsbexchange-com1.p.rapidapi.com/v2/registration/N12345'"
                )
