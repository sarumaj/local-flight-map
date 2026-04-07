import asyncio
from types import TracebackType
from typing import Optional, Self, cast

from async_lru import alru_cache
from cloudscraper import create_scraper  # type: ignore[reportMissingTypeStubs]
from lxml import html  # type: ignore[reportMissingTypeStubs]

from .config import JetPhotosConfig
from .response import JetPhotosResponse


class JetPhotosClient:
    """
    Client for interacting with the Jet Photos service.

    This class provides methods for fetching aircraft, route, and airport information
    from the Jet Photos service. It includes caching to improve performance and reduce API calls.

    The client supports:
    - Fetching aircraft photo
    """

    def __init__(self, config: Optional[JetPhotosConfig] = None):
        """
        Initialize a new Jet Photos client.

        Args:
            config: Optional configuration for the client. If not provided,
                   default configuration will be used.
        """
        self._config = config or JetPhotosConfig()
        self._scrapper = create_scraper()  # type: ignore[reportUnknownType]
        self._scraper_lock = asyncio.Lock()

    async def __aenter__(self) -> Self:
        """
        Enter the async context manager.

        Returns:
            self: The initialized client instance
        """
        return self

    async def __aexit__(
        self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]
    ):
        """
        Exit the async context manager.
        Closes the HTTP session.

        Args:
            exc_type: The type of exception that was raised, if any
            exc_val: The exception value that was raised, if any
            exc_tb: The traceback of the exception, if any
        """
        _ = (exc_type, exc_val, exc_tb)
        self._scrapper.close()

    def _find_elem_by_xpath(self, body: str, xpath: str) -> Optional[str]:
        """
        Helper method to find an element in the HTML response using XPath.

        Args:
            body: The HTML content as a string
            xpath: The XPath expression to locate the desired element

        Returns:
            The text content of the found element, or None if not found
        """

        tree = cast(
            html.HtmlElement,
            html.fromstring(body),  # type: ignore[reportUnknownMemberType]
        )
        return cast(
            Optional[str],
            next(
                iter(tree.xpath(xpath)),  # type: ignore[reportUnknownMemberType,reportUnknownArgumentType]
                None,
            ),
        )

    @alru_cache(maxsize=25)
    async def get_aircraft_photo(self, registration: str) -> Optional[JetPhotosResponse]:
        """
        Fetch the photo URL for a given aircraft registration.

        Args:
            registration: The registration of the aircraft. Example: "N12345"

        Returns:
            The photo data as bytes if found, otherwise None.
        """

        def _get_aircraft_photo_sync(registration: str) -> Optional[JetPhotosResponse]:
            response = self._scrapper.get(
                self._config.jet_base_url.removesuffix("/") + "/showphotos.php",
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
                timeout=self._config.http_total_timeout,
            )
            response.raise_for_status()

            link: str = ""
            for xpath, relative in (
                ("(//div[@class='results']/div[@class='result']//a[@class='result__photoLink'])[1]/@href", True),
                ("//div[@class='large-photo-container']//a[@id='show-large-photo']/img/@src", False),
            ):
                link = self._find_elem_by_xpath(response.text, xpath)
                if not link:
                    return None

                if relative:
                    link = self._config.jet_base_url.removesuffix("/") + link

                response = self._scrapper.get(link, timeout=self._config.http_total_timeout)
                response.raise_for_status()

            return JetPhotosResponse(
                registration=registration,
                photo_url=link,
                photo_data=response.content,
                content_type=response.headers.get("Content-Type", "application/octet-stream").split(";")[0],
            )

        async with self._scraper_lock:
            result = await asyncio.to_thread(_get_aircraft_photo_sync, registration)
        return result
