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
        assert json_str == '{"name": "test", "value": 42}'

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
            'raise_for_status': mock_raise_for_status
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
            'json': mock_json
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
