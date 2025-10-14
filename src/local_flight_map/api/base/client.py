from types import TracebackType
from typing import Any, Dict, Optional

import aiohttp

from .config import BaseConfig


class BaseClient:
    """
    Base class for API clients.
    Provides common functionality for making HTTP requests and managing sessions.
    """

    def __init__(self, config: Optional[BaseConfig] = None, **session_params: Any):
        """
        Initialize the API client.

        Args:
            config: Optional configuration object
            session_params: Additional parameters for the aiohttp session
        """
        self._config = config or BaseConfig()
        self._session_params = session_params

        # Create timeout configuration
        timeout = aiohttp.ClientTimeout(
            connect=self._config.http_connect_timeout,
            total=self._config.http_total_timeout,
            sock_connect=self._config.http_connect_timeout,
            sock_read=self._config.http_total_timeout,
        )

        # Update session parameters with timeout
        session_params_with_timeout: Dict[str, Any] = {"timeout": timeout}
        session_params_with_timeout.update(self._session_params)

        self._session = aiohttp.ClientSession(**session_params_with_timeout)

    async def close(self):
        """
        Close the client's HTTP session.
        """
        if hasattr(self, "_session"):
            await self._session.close()
            del self._session

    async def __aenter__(self) -> "BaseClient":
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
        await self.close()

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Optional[Dict[str, Any]]:
        """
        Handle HTTP response and return JSON data if successful.

        Args:
            response: The aiohttp response object.

        Returns:
            Optional[Dict]: The JSON response data if successful, None otherwise.

        Raises:
            aiohttp.ClientResponseError: If the response indicates an error.
        """
        if response.status == 404:
            return None

        response.raise_for_status()

        # Pass the content type to the json method to avoid errors
        # when the content type is not application/json
        # (opensky feeder returns text/html, even though it is JSON)
        return await response.json(content_type=response.content_type)
