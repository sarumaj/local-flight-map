import pytest
import math
import aiohttp
from dataclasses import dataclass
from unittest.mock import AsyncMock, Mock
from local_flight_map.api.base import Location, BBox, ResponseObject, BaseClient


class TestLocation:
    def test_location_creation(self):
        location = Location(latitude=51.5074, longitude=-0.1278)
        assert location.latitude == 51.5074
        assert location.longitude == -0.1278

    def test_location_immutability(self):
        location = Location(latitude=51.5074, longitude=-0.1278)
        with pytest.raises(AttributeError):
            location.latitude = 52.0

    def test_location_get_angle_to(self):
        """Test the get_angle_to method of Location class."""
        # Test case 1: North bearing (0 degrees)
        loc1 = Location(latitude=0, longitude=0)
        loc2 = Location(latitude=1, longitude=0)
        assert loc1.get_angle_to(loc2) == pytest.approx(0, abs=0.01)

        # Test case 2: East bearing (90 degrees)
        loc1 = Location(latitude=0, longitude=0)
        loc2 = Location(latitude=0, longitude=1)
        assert loc1.get_angle_to(loc2) == pytest.approx(90, abs=0.01)

        # Test case 3: South bearing (180 degrees)
        loc1 = Location(latitude=0, longitude=0)
        loc2 = Location(latitude=-1, longitude=0)
        assert loc1.get_angle_to(loc2) == pytest.approx(180, abs=0.01)

        # Test case 4: West bearing (270 degrees)
        loc1 = Location(latitude=0, longitude=0)
        loc2 = Location(latitude=0, longitude=-1)
        assert loc1.get_angle_to(loc2) == pytest.approx(270, abs=0.01)

        # Test case 5: Northeast bearing (45 degrees)
        loc1 = Location(latitude=0, longitude=0)
        loc2 = Location(latitude=1, longitude=1)
        # Due to Earth's curvature, the bearing isn't exactly 45 degrees
        assert loc1.get_angle_to(loc2) == pytest.approx(45, abs=0.01)

        # Test case 6: Northwest bearing (315 degrees)
        loc1 = Location(latitude=0, longitude=0)
        loc2 = Location(latitude=1, longitude=-1)
        assert loc1.get_angle_to(loc2) == pytest.approx(315, abs=0.01)

        # Test case 7: Southeast bearing (135 degrees)
        loc1 = Location(latitude=0, longitude=0)
        loc2 = Location(latitude=-1, longitude=1)
        assert loc1.get_angle_to(loc2) == pytest.approx(135, abs=0.01)

        # Test case 8: Southwest bearing (225 degrees)
        loc1 = Location(latitude=0, longitude=0)
        loc2 = Location(latitude=-1, longitude=-1)
        assert loc1.get_angle_to(loc2) == pytest.approx(225, abs=0.01)

        # Test case 9: Same location (should be 0 degrees)
        loc1 = Location(latitude=45, longitude=-120)
        assert loc1.get_angle_to(loc1) == pytest.approx(0, abs=0.01)

        # Test case 10: Real-world example (San Francisco to New York)
        sf = Location(latitude=37.7749, longitude=-122.4194)
        ny = Location(latitude=40.7128, longitude=-74.0060)
        # Expected bearing is approximately 70 degrees (northeast)
        assert sf.get_angle_to(ny) == pytest.approx(70, abs=1)

        # Test case 11: Cross the international date line
        loc1 = Location(latitude=0, longitude=179)
        loc2 = Location(latitude=0, longitude=-179)
        # Should calculate the shorter path across the date line
        assert loc1.get_angle_to(loc2) == pytest.approx(90, abs=0.01)

        # Test case 12: Near the poles
        loc1 = Location(latitude=89, longitude=0)
        loc2 = Location(latitude=89.5, longitude=90)  # Moving both north and east
        # At high latitudes, the bearing should be approximately 26.57 degrees
        # This is because the great circle path curves significantly towards the pole
        assert loc1.get_angle_to(loc2) == pytest.approx(26.57, abs=0.01)

        # Test case 13: Pure eastward movement at high latitude
        loc1 = Location(latitude=89, longitude=0)
        loc2 = Location(latitude=89, longitude=1)  # Moving only east by 1 degree
        # The initial bearing should be approximately east
        assert loc1.get_angle_to(loc2) == pytest.approx(90, abs=1)


class TestBBox:
    def test_bbox_creation(self):
        bbox = BBox(min_lat=50.0, max_lat=52.0, min_lon=-1.0, max_lon=1.0)
        assert bbox.min_lat == 50.0
        assert bbox.max_lat == 52.0
        assert bbox.min_lon == -1.0
        assert bbox.max_lon == 1.0

    def test_bbox_immutability(self):
        bbox = BBox(min_lat=50.0, max_lat=52.0, min_lon=-1.0, max_lon=1.0)
        with pytest.raises(AttributeError):
            bbox.min_lat = 51.0

    def test_get_bbox_by_radius(self):
        center = Location(latitude=51.5074, longitude=-0.1278)
        radius = 10  # nautical miles
        bbox = BBox.get_bbox_by_radius(center, radius)

        # Calculate expected values
        lat_degrees = radius / 60
        lon_degrees = radius / 60 / math.cos(math.radians(center.latitude))

        assert abs(bbox.min_lat - (center.latitude - lat_degrees)) < 0.0001
        assert abs(bbox.max_lat - (center.latitude + lat_degrees)) < 0.0001
        assert abs(bbox.min_lon - (center.longitude - lon_degrees)) < 0.0001
        assert abs(bbox.max_lon - (center.longitude + lon_degrees)) < 0.0001

    def test_get_bbox_by_radius_negative_radius(self):
        center = Location(latitude=51.5074, longitude=-0.1278)
        with pytest.raises(ValueError, match="Radius must be non-negative"):
            BBox.get_bbox_by_radius(center, -10)

    def test_get_bbox_by_radius_pole(self):
        center = Location(latitude=90.0, longitude=0.0)
        with pytest.raises(ValueError, match="Cannot calculate bounding box near the poles"):
            BBox.get_bbox_by_radius(center, 10)

    def test_get_bbox_by_radius_boundaries(self):
        # Test near the equator
        center = Location(latitude=0.0, longitude=0.0)
        bbox = BBox.get_bbox_by_radius(center, 1000)
        assert bbox.min_lat >= -90
        assert bbox.max_lat <= 90
        assert bbox.min_lon >= -180
        assert bbox.max_lon <= 180


class TestResponseObject:
    @dataclass
    class SampleResponse(ResponseObject):
        name: str
        value: int

    def test_to_dict(self):
        obj = self.SampleResponse(name="test", value=42)
        data = obj.to_dict()
        assert data == {"name": "test", "value": 42}

    def test_from_dict(self):
        data = {"name": "test", "value": 42}
        obj = self.SampleResponse.from_dict(data)
        assert obj.name == "test"
        assert obj.value == 42

    def test_to_json(self):
        obj = self.SampleResponse(name="test", value=42)
        json_str = obj.to_json()
        assert json_str == '{"name":"test","value":42}'

    def test_from_json(self):
        json_str = '{"name": "test", "value": 42}'
        obj = self.SampleResponse.from_json(json_str)
        assert obj.name == "test"
        assert obj.value == 42

    def test_from_list(self):
        data = ["test", 42]
        obj = self.SampleResponse.from_list(data)
        assert obj.name == "test"
        assert obj.value == 42


class TestBaseClient:
    @pytest.mark.asyncio
    async def test_context_manager(self):
        client = BaseClient()
        async with client as c:
            assert c._session is not None
            assert isinstance(c._session, aiohttp.ClientSession)
        assert client._session is None

    @pytest.mark.asyncio
    async def test_handle_response_404(self):
        client = BaseClient()
        mock_raise_for_status = Mock(return_value=None)
        mock_response = type('MockResponse', (), {
            'status': 404,
            'raise_for_status': mock_raise_for_status,
            'content_type': "application/json"
        })
        result = await client._handle_response(mock_response)
        assert result is None
        mock_raise_for_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_response_success(self):
        client = BaseClient()
        mock_json = AsyncMock(return_value={'data': 'test'})
        mock_raise_for_status = Mock(return_value=None)
        mock_response = type('MockResponse', (), {
            'status': 200,
            'raise_for_status': mock_raise_for_status,
            'json': mock_json,
            'content_type': "application/json"
        })
        result = await client._handle_response(mock_response)
        assert result == {'data': 'test'}
        mock_json.assert_called_once()
        mock_raise_for_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_response_error(self):
        client = BaseClient()
        mock_raise_for_status = Mock(side_effect=aiohttp.ClientResponseError(
            request_info=None,
            history=None,
            status=500
        ))
        mock_response = type('MockResponse', (), {
            'status': 500,
            'raise_for_status': mock_raise_for_status,
        })
        with pytest.raises(aiohttp.ClientResponseError):
            await client._handle_response(mock_response)
        mock_raise_for_status.assert_called_once()
