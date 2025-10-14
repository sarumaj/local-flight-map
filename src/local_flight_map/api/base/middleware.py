import logging
from base64 import b64encode
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiohttp
import orjson as json

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class OAuth2AuthMiddleware:
    """
    Middleware for adding OAuth2 authentication to requests.

    This middleware adds an OAuth2 access token to the request headers if
    the request does not already have an Authorization header.
    """

    def __init__(
        self,
        *,
        auth_url: str,
        client_id: str,
        client_secret: str,
        grant_type: str = "client_credentials",
        timeout: Optional[aiohttp.ClientTimeout] = None,
    ):
        """
        Initialize the OAuth2 authentication middleware.

        Args:
            auth_url: The URL for the OAuth2 token endpoint.
            client_id: The OAuth2 client ID.
            client_secret: The OAuth2 client secret.
            grant_type: The OAuth2 grant type. Defaults to "client_credentials".
            timeout: Optional timeout configuration for authentication requests.
        """
        self._auth_url = auth_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._grant_type = grant_type
        self._timeout = timeout
        self._access_token = None
        self._token_expiry = 0
        self._token_storage_path = Path.home() / "{identifier}.oauth2_token.json".format(
            identifier=b64encode((self._auth_url + ":" + self._client_id).encode()).decode()
        )
        if self._token_storage_path.exists() and self._token_storage_path.is_file():
            try:
                data = json.loads(self._token_storage_path.read_bytes())
                self._access_token = data.get("access_token")
                self._token_expiry = data.get("token_expiry", 0)
            except (json.JSONDecodeError, KeyError):
                pass
        self._logger = logging.getLogger("local_flight_map.api.OAuth2AuthMiddleware")

    async def _get_access_token(self) -> Optional[str]:
        """
        Get a valid OAuth2 access token using client credentials flow.
        If the current token is still valid, it will be returned.
        Otherwise, a new token will be requested.

        Returns:
            Optional[str]: A valid access token.

        Raises:
            ValueError: If client credentials are not configured.
        """
        # Require both client_id and client_secret
        if not self._client_id or not self._client_secret:
            self._logger.warning("OAuth2 client credentials not configured (client_id or client_secret missing)")
            return None

        now = int(datetime.now().timestamp())
        if self._access_token and now < self._token_expiry:
            return self._access_token

        # Create session with timeout if provided
        session_kwargs = {}
        if self._timeout:
            session_kwargs["timeout"] = self._timeout

        async with aiohttp.ClientSession(**session_kwargs) as session:  # pyright: ignore[reportUnknownArgumentType]
            try:
                resp = await session.post(
                    self._auth_url,
                    data={
                        "grant_type": self._grant_type,
                        "client_id": self._client_id,
                        "client_secret": self._client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
            except Exception as e:
                self._logger.error("Failed to connect to token endpoint %s", self._auth_url, exc_info=True)
                raise ValueError("Failed to connect to token endpoint") from e

            # If we have a response object, check status and parse JSON
            try:
                resp.raise_for_status()
            except aiohttp.ClientResponseError as e:
                self._logger.error(
                    "Non-200 response from token endpoint %s: %s",
                    self._auth_url,
                    resp.status,
                    exc_info=True,
                )
                raise ValueError(f"Failed to get access token: {resp.status}") from e

            try:
                data = await resp.json()
            except Exception as e:  # JSON decoding error or similar
                self._logger.error("Failed to decode JSON from token endpoint %s", self._auth_url, exc_info=True)
                raise ValueError("Invalid JSON response from token endpoint") from e

            try:
                self._access_token = data["access_token"]
                self._token_expiry = now + int(data.get("expires_in", 0))
            except KeyError as e:
                self._logger.error(
                    "Token response missing expected fields from %s: %s", self._auth_url, data, exc_info=True
                )
                raise ValueError("Token response missing access_token") from e

            try:
                self._token_storage_path.write_bytes(
                    json.dumps(
                        {"access_token": self._access_token, "token_expiry": self._token_expiry},
                        option=json.OPT_INDENT_2,
                    )
                )
            except Exception:
                self._logger.warning("Failed to persist token to %s", self._token_storage_path, exc_info=True)

            return self._access_token

    async def __call__(
        self, request: aiohttp.ClientRequest, handler: aiohttp.ClientHandlerType
    ) -> aiohttp.ClientResponse:
        """
        Method to be called by the client.

        Args:
            request: The request to add the OAuth2 access token to.
            handler: The handler to call the request with.

        Returns:
            The response from the handler.
        """
        if request.headers.get("Authorization"):
            raise ValueError("Authorization header already set")

        if token := await self._get_access_token():
            request.headers["Authorization"] = f"Bearer {token}"

        return await handler(request)
