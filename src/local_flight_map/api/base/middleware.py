import aiohttp
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class OAuth2AuthMiddleware:
    """
    Middleware for adding OAuth2 authentication to requests.

    This middleware adds an OAuth2 access token to the request headers if
    the request does not already have an Authorization header.
    """
    def __init__(
        self, *,
        auth_url: str,
        client_id: str,
        client_secret: str,
        grant_type: str = "client_credentials"
    ):
        """
        Initialize the OAuth2 authentication middleware.

        Args:
            auth_url: The URL for the OAuth2 token endpoint.
            client_id: The OAuth2 client ID.
            client_secret: The OAuth2 client secret.
            grant_type: The OAuth2 grant type. Defaults to "client_credentials".
        """
        self._auth_url = auth_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._grant_type = grant_type
        self._access_token = None
        self._token_expiry = 0
        self._logger = logging.getLogger("local_flight_map.api.OAuth2AuthMiddleware")

    async def _get_access_token(self) -> str:
        """
        Get a valid OAuth2 access token using client credentials flow.
        If the current token is still valid, it will be returned.
        Otherwise, a new token will be requested.

        Returns:
            str: A valid access token.

        Raises:
            ValueError: If client credentials are not configured.
        """
        if not self._client_id and not self._client_secret:
            self._logger.warning("OAuth2 client credentials not configured")
            return None

        now = int(datetime.now().timestamp())
        if self._access_token and now < self._token_expiry:
            return self._access_token

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                self._auth_url,
                data={
                    "grant_type": self._grant_type,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret
                }
            ) as response
        ):
            try:
                response.raise_for_status()
            except aiohttp.ClientResponseError as e:
                raise ValueError(f"Failed to get access token: {response.status}") from e
            else:
                data = await response.json()
                self._access_token = data["access_token"]
                self._token_expiry = now + data["expires_in"]
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
        if not request.headers:
            request.headers = {}

        if request.headers.get("Authorization"):
            raise ValueError("Authorization header already set")

        if token := await self._get_access_token():
            request.headers["Authorization"] = f"Bearer {token}"

        return await handler(request)
