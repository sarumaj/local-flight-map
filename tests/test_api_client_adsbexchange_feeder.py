import pytest
import aiohttp
from unittest.mock import AsyncMock, Mock, patch
from local_flight_map.api.adsbexchange.feed import (
    AdsbExchangeFeederClient,
    AdsbExchangeFeederConfig,
    AdsbExchangeFeederResponse,
    AircraftPropertiesFromFeeder,
)


@pytest.fixture
async def adsbexchange_feeder_client():
    config = AdsbExchangeFeederConfig(
        adsbexchange_feeder_uuid="test-uuid"
    )
    with patch('async_lru._LRUCacheWrapper.cache_close') as close:
        close.return_value = AsyncMock()
        client = AdsbExchangeFeederClient(config)
        yield client
        await client.close()


@pytest.fixture
async def adsbexchange_feeder_client_empty():
    config = AdsbExchangeFeederConfig(
        adsbexchange_feeder_uuid=""
    )
    with patch('async_lru._LRUCacheWrapper.cache_close') as close:
        close.return_value = AsyncMock()
        client = AdsbExchangeFeederClient(config)
        yield client
        await client.close()


def get_mock_aircraft_data():
    """Helper function to get complete mock aircraft data"""
    return {
        "hex": "a83547",
        "type": "adsb_icao",
        "flight": "SWA123",
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
        "r_dst": 100.0,
        "r_dir": 45.0,
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
        "rssi": -20.0,
        "calc_track": 90.0,
        "lastPosition": {
            "lat": 40.6413,
            "lon": -73.7781,
            "nic": 8,
            "rc": 185,
            "seen_pos": 0.0
        }
    }


def get_mock_response_data():
    """Helper function to get complete mock response data"""
    return {
        "aircraft": [get_mock_aircraft_data()],
        "messages": "No error",
        "now": 1678901234
    }


class TestAdsbExchangeFeederClient:
    @pytest.mark.asyncio
    async def test_get_aircraft_from_adsbexchange_feeder(self, adsbexchange_feeder_client):
        # Mock response data
        mock_data = get_mock_response_data()

        # Mock the session's get method
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_data)
        mock_response.raise_for_status = Mock(return_value=None)
        mock_response.content_type = "text/html"

        with patch.object(adsbexchange_feeder_client, '_session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.close = AsyncMock()

            async with adsbexchange_feeder_client:
                # Test the method
                result = await adsbexchange_feeder_client.get_aircraft_from_adsbexchange_feeder()

                # Verify the result
                assert isinstance(result, AdsbExchangeFeederResponse)
                assert result.messages == "No error"
                assert result.now == 1678901234

                assert len(result.aircraft) == 1
                aircraft = result.aircraft[0]
                assert isinstance(aircraft, AircraftPropertiesFromFeeder)
                assert aircraft.hex == "a83547"
                assert aircraft.type == "adsb_icao"
                assert aircraft.flight == "SWA123"
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
                assert aircraft.r_dst == 100.0
                assert aircraft.r_dir == 45.0
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
                assert aircraft.calc_track == 90.0
                assert aircraft.lastPosition == {
                    "lat": 40.6413,
                    "lon": -73.7781,
                    "nic": 8,
                    "rc": 185,
                    "seen_pos": 0.0
                }

                # Verify the API call
                mock_session.get.assert_called_once_with(
                    "/uuid/?feed=test-uuid"
                )

    @pytest.mark.asyncio
    async def test_get_aircraft_from_adsbexchange_feeder_no_uuid(self, adsbexchange_feeder_client_empty):
        # Test that it raises ValueError
        with pytest.raises(ValueError):
            await adsbexchange_feeder_client_empty.get_aircraft_from_adsbexchange_feeder()

    @pytest.mark.asyncio
    async def test_get_aircraft_from_adsbexchange_feeder_not_found(self, adsbexchange_feeder_client):
        # Mock the session's get method to return 404
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.raise_for_status = Mock(side_effect=aiohttp.ClientResponseError(
            request_info=Mock(),
            history=(),
            status=404,
            message="Not Found",
            headers={}
        ))
        mock_response.content_type = "text/html"

        with patch.object(adsbexchange_feeder_client, '_session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.close = AsyncMock()

            async with adsbexchange_feeder_client:
                # Test the method
                result = await adsbexchange_feeder_client.get_aircraft_from_adsbexchange_feeder()
                assert result is None


class TestAircraftPropertiesFromFeeder:
    def test_to_geojson(self):
        # Create test data
        aircraft_data = get_mock_aircraft_data()
        aircraft = AircraftPropertiesFromFeeder.from_dict(aircraft_data)

        # Test to_geojson method
        geojson = aircraft.to_geojson()

        # Verify the result
        assert geojson is not None
        assert geojson["type"] == "Feature"
        assert geojson["geometry"]["type"] == "Point"
        assert geojson["geometry"]["coordinates"] == [-73.7781, 40.6413]
        assert geojson["properties"]["icao24_code"] == "a83547"
        assert geojson["properties"]["callsign"] == "SWA123"
        assert geojson["properties"]["baro_altitude"] == 35000
        assert geojson["properties"]["geom_altitude"] == 35000
        assert geojson["properties"]["ground_speed"] == 250.0
        assert geojson["properties"]["indicated_airspeed"] == 240.0
        assert geojson["properties"]["true_airspeed"] == 245.0
        assert geojson["properties"]["mach"] == 0.78
        assert geojson["properties"]["wind_direction"] == 270.0
        assert geojson["properties"]["wind_speed"] == 50.0
        assert geojson["properties"]["outside_air_temperature"] == -50.0
        assert geojson["properties"]["total_air_temperature"] == -45.0
        assert geojson["properties"]["track_angle"] == 90.0
        assert geojson["properties"]["track_rate"] == 0.0
        assert geojson["properties"]["roll_angle"] == 0.0
        assert geojson["properties"]["magnetic_heading"] == 90.0
        assert geojson["properties"]["true_heading"] == 90.0
        assert geojson["properties"]["baro_rate_of_climb_descent"] == 0.0
        assert geojson["properties"]["geom_rate_of_climb_descent"] == 0.0
        assert geojson["properties"]["squawk_code"] == "1234"
        assert geojson["properties"]["emergency_status"] == "none"
        assert geojson["properties"]["category"] == "A3"
        assert geojson["properties"]["qnh_pressure"] == 1013.2
        assert geojson["properties"]["mcp_altitude"] == 35000
        assert geojson["properties"]["fms_altitude"] == 35000
        assert geojson["properties"]["heading"] == 90.0
        assert geojson["properties"]["navigation_modes"] == ["autopilot", "vnav"]
        assert geojson["properties"]["latitude"] == 40.6413
        assert geojson["properties"]["longitude"] == -73.7781
        assert geojson["properties"]["navigation_integrity_category"] == 8
        assert geojson["properties"]["radius_of_containment"] == 185
        assert geojson["properties"]["time_since_last_position_update"] == 0.0
        assert geojson["properties"]["distance_from_receiver"] == 100.0
        assert geojson["properties"]["direction_from_receiver"] == 45.0
        assert geojson["properties"]["version"] == 2
        assert geojson["properties"]["baro_navigation_integrity_category"] == 1
        assert geojson["properties"]["navigation_accuracy_category_for_position"] == 9
        assert geojson["properties"]["navigation_accuracy_category_for_velocity"] == 1
        assert geojson["properties"]["surveillance_integrity_level"] == 3
        assert geojson["properties"]["surveillance_integrity_level_type"] == "perhour"
        assert geojson["properties"]["geometric_vertical_accuracy"] == 2
        assert geojson["properties"]["system_design_assurance"] == 2
        assert geojson["properties"]["alert_flag"] == 0
        assert geojson["properties"]["special_position_indicator_flag"] == 0
        assert geojson["properties"]["multilateration_sources"] == []
        assert geojson["properties"]["tisb_sources"] == []
        assert geojson["properties"]["number_of_messages_received"] == 100
        assert geojson["properties"]["time_since_last_update"] == 0.0
        assert geojson["properties"]["received_signal_strength_indicator"] == -20.0
        assert geojson["properties"]["calculated_track"] == 90.0
        assert geojson["properties"]["is_last_position"] is True

    def test_to_geojson_no_position(self):
        # Create test data without position
        aircraft_data = get_mock_aircraft_data()
        aircraft_data.pop("lat")
        aircraft_data.pop("lon")
        aircraft_data.pop("lastPosition")
        aircraft = AircraftPropertiesFromFeeder.from_dict(aircraft_data)

        # Test to_geojson method
        geojson = aircraft.to_geojson()

        # Verify the result
        assert geojson is None

    def test_to_geojson_with_last_position(self):
        # Create test data with only lastPosition
        aircraft_data = get_mock_aircraft_data()
        aircraft_data.pop("lat")
        aircraft_data.pop("lon")
        aircraft = AircraftPropertiesFromFeeder.from_dict(aircraft_data)

        # Test to_geojson method
        geojson = aircraft.to_geojson()

        # Verify the result
        assert geojson is not None
        assert geojson["geometry"]["coordinates"] == [-73.7781, 40.6413]
        assert geojson["properties"]["navigation_integrity_category"] == 8
        assert geojson["properties"]["radius_of_containment"] == 185
        assert geojson["properties"]["time_since_last_position_update"] == 0.0
        assert geojson["properties"]["is_last_position"] is True


class TestAdsbExchangeFeederResponse:
    def test_to_geojson(self):
        # Create test data
        response_data = get_mock_response_data()
        response = AdsbExchangeFeederResponse.from_dict(response_data)

        # Test to_geojson method
        geojson = response.to_geojson()

        # Verify the result
        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) == 1
        assert geojson["features"][0]["type"] == "Feature"
        assert geojson["features"][0]["geometry"]["type"] == "Point"
        assert geojson["features"][0]["geometry"]["coordinates"] == [-73.7781, 40.6413]
        assert geojson["features"][0]["properties"]["icao24_code"] == "a83547"
        assert geojson["features"][0]["properties"]["callsign"] == "SWA123"

    def test_to_geojson_empty_aircraft(self):
        # Create test data with empty aircraft list
        response_data = {
            "aircraft": [],
            "messages": "No error",
            "now": 1678901234
        }
        response = AdsbExchangeFeederResponse.from_dict(response_data)

        # Test to_geojson method
        geojson = response.to_geojson()

        # Verify the result
        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) == 0
