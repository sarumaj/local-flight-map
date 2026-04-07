# type: basic
from typing import Iterator
from unittest.mock import Mock, call, patch

import pytest

from local_flight_map.api.jetphotos import JetPhotosClient, JetPhotosConfig, JetPhotosResponse


@pytest.fixture
def jetphotos_client() -> Iterator[tuple[JetPhotosClient, Mock]]:
    with patch("local_flight_map.api.jetphotos.client.create_scraper") as mock_create_scraper:
        mock_scraper = Mock()
        mock_create_scraper.return_value = mock_scraper
        client = JetPhotosClient(JetPhotosConfig())
        yield client, mock_scraper


def _mock_response(*, text: str = "", content: bytes = b"", content_type: str = "application/octet-stream") -> Mock:
    response = Mock()
    response.text = text
    response.content = content
    response.headers = {"Content-Type": content_type}
    response.raise_for_status = Mock(return_value=None)
    return response


class TestJetPhotosClient:

    async def test_get_aircraft_photo(self, jetphotos_client: tuple[JetPhotosClient, Mock]):
        client, mock_scraper = jetphotos_client
        registration = "N12345"

        search_page = _mock_response(
            text="""
                <div class=\"results\">
                  <div class=\"result\"><a class=\"result__photoLink\" href=\"/photo/123\"></a></div>
                </div>
            """
        )
        details_page = _mock_response(
            text="""
                <div class=\"large-photo-container\">
                  <a id=\"show-large-photo\"><img src=\"https://cdn.jetphotos.com/fullsize.jpg\" /></a>
                </div>
            """
        )
        image_response = _mock_response(content=b"image-bytes", content_type="image/jpeg; charset=utf-8")

        mock_scraper.get.side_effect = [search_page, details_page, image_response]

        result = await client.get_aircraft_photo(registration)

        assert isinstance(result, JetPhotosResponse)
        assert result.registration == registration
        assert result.photo_url == "https://cdn.jetphotos.com/fullsize.jpg"
        assert result.photo_data == b"image-bytes"
        assert result.content_type == "image/jpeg"

        config = client._config  # type: ignore[reportPrivateUsage]
        expected_search_url = config.jet_base_url.removesuffix("/") + "/showphotos.php"
        expected_details_url = config.jet_base_url.removesuffix("/") + "/photo/123"
        timeout = config.http_total_timeout

        mock_scraper.get.assert_has_calls(
            [
                call(
                    expected_search_url,
                    params={
                        "aircraft": "all",
                        "airline": "all",
                        "category": "all",
                        "country-location": "all",
                        "genre": "all",
                        "keywords-contain": 3,
                        "keywords-type": "reg",
                        "keywords": registration,
                        "photo-year": "all",
                        "photographer-group": "all",
                        "search-type": "Advanced",
                        "sort-order": 2,
                        "page": 1,
                    },
                    timeout=timeout,
                ),
                call(expected_details_url, timeout=timeout),
                call("https://cdn.jetphotos.com/fullsize.jpg", timeout=timeout),
            ]
        )

    async def test_get_aircraft_photo_not_found_on_search_page(self, jetphotos_client: tuple[JetPhotosClient, Mock]):
        client, mock_scraper = jetphotos_client

        search_page = _mock_response(text="<html><body><div>No matches</div></body></html>")
        mock_scraper.get.return_value = search_page

        result = await client.get_aircraft_photo("N00000")

        assert result is None
        assert mock_scraper.get.call_count == 1

    async def test_get_aircraft_photo_not_found_on_details_page(self, jetphotos_client: tuple[JetPhotosClient, Mock]):
        client, mock_scraper = jetphotos_client

        search_page = _mock_response(
            text="""
                <div class=\"results\">
                  <div class=\"result\"><a class=\"result__photoLink\" href=\"/photo/123\"></a></div>
                </div>
            """
        )
        details_page = _mock_response(text="<html><body><div>No image</div></body></html>")

        mock_scraper.get.side_effect = [search_page, details_page]

        result = await client.get_aircraft_photo("N12345")

        assert result is None
        assert mock_scraper.get.call_count == 2

    async def test_get_aircraft_photo_error_propagation(self, jetphotos_client: tuple[JetPhotosClient, Mock]):
        client, mock_scraper = jetphotos_client

        search_page = _mock_response()
        search_page.raise_for_status.side_effect = RuntimeError("JetPhotos unavailable")
        mock_scraper.get.return_value = search_page

        with pytest.raises(RuntimeError, match="JetPhotos unavailable"):
            await client.get_aircraft_photo("N12345")

    async def test_get_aircraft_photo_is_cached(self, jetphotos_client: tuple[JetPhotosClient, Mock]):
        client, mock_scraper = jetphotos_client

        search_page = _mock_response(
            text="""
                <div class=\"results\">
                  <div class=\"result\"><a class=\"result__photoLink\" href=\"/photo/123\"></a></div>
                </div>
            """
        )
        details_page = _mock_response(
            text="""
                <div class=\"large-photo-container\">
                  <a id=\"show-large-photo\"><img src=\"https://cdn.jetphotos.com/fullsize.jpg\" /></a>
                </div>
            """
        )
        image_response = _mock_response(content=b"image-bytes", content_type="image/jpeg")

        mock_scraper.get.side_effect = [search_page, details_page, image_response]

        first = await client.get_aircraft_photo("N12345")
        second = await client.get_aircraft_photo("N12345")

        assert first is second
        assert mock_scraper.get.call_count == 3

    async def test_context_manager_closes_scraper(self, jetphotos_client: tuple[JetPhotosClient, Mock]):
        client, mock_scraper = jetphotos_client

        async with client:
            pass

        mock_scraper.close.assert_called_once()
