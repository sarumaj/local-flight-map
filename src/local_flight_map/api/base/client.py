from typing import Optional, Any, Dict
import aiohttp

from .config import BaseConfig


class BaseClient:
    """
    Base class for API clients.
    Provides common functionality for making HTTP requests and managing sessions.
    """
    def __init__(
        self,
        config: Optional[BaseConfig] = None,
        **session_params: Dict[str, Any]
    ):
        """
        Initialize the API client.

        Args:
            config: Optional configuration object
            session_params: Additional parameters for the aiohttp session
        """
        self._config = config or BaseConfig()
        self._session_params = session_params
        self._session = aiohttp.ClientSession(**self._session_params)

    async def close(self):
        """
        Close the client's HTTP session.
        """
        if self._session:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> 'BaseClient':
        """
        Enter the async context manager.

        Returns:
            self: The initialized client instance
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
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

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Optional[Any]:
        """
        Handle an HTTP response from the API.

        Args:
            response: The HTTP response to handle

        Returns:
            The parsed JSON response, or None if the response was 404

        Raises:
            aiohttp.ClientError: If the response indicates an error
        """
        if response.status == 404:
            return None

        response.raise_for_status()
        return await response.json(content_type=response.content_type) or None
