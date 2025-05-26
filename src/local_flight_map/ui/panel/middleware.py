"""
Middleware module for the Local Flight Map application.
Provides authentication and request logging middleware.
"""

import re
import time
import fastapi
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from typing import Callable, Dict

from .config import logger


class SessionAuthenticator(BaseHTTPMiddleware):
    """
    Session authenticator middleware.
    Handles authentication for protected routes.
    """
    def __init__(self, app: fastapi.FastAPI, paths: Dict[re.Pattern, Response] = None):
        """
        Initialize the session authenticator.

        Args:
            app: The FastAPI app to add middleware to.
            paths: Dictionary mapping regex patterns to responses for path-based authentication.
        """
        BaseHTTPMiddleware.__init__(self, app)
        self._paths = paths

    async def dispatch(self, request: Request, call_next: Callable) -> fastapi.Response:
        """
        Process the request and handle authentication.

        Args:
            request: The incoming request.
            call_next: The next middleware in the chain.

        Returns:
            The response from the next middleware or an authentication response.
        """
        for path, response in (
            self._paths or {
                re.compile(r"^/.*"): JSONResponse(
                    content={"error": "Unauthorized"},
                    status_code=200,
                    headers={"X-Status-Code": "403"}
                )
            }
        ).items():
            if path.match(request.url.path):
                if "authenticated" not in request.session:
                    logger.warning(f"Unauthenticated request to {request.url.path}")
                    request.session["authenticated"] = True
                    return response
        
        return await call_next(request)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """
    Request logger middleware.
    Logs information about each request including timing and response size.
    """
    def __init__(self, app: fastapi.FastAPI):
        """
        Initialize the request logger middleware.

        Args:
            app: The FastAPI app to add middleware to.
        """
        BaseHTTPMiddleware.__init__(self, app)

    async def dispatch(self, request: Request, call_next: Callable) -> fastapi.Response:
        """
        Process the request and log information about it.

        Args:
            request: The incoming request.
            call_next: The next middleware in the chain.

        Returns:
            The response from the next middleware.
        """
        start_time = time.time()
        response = await call_next(request)
        end_time = time.time()
        diff = end_time - start_time
        size = response.headers.get("Content-Length", 0)
        logger.info(
            f"{request.method} {request.url.path}: "
            f"{response.status_code}: {int(size)/1024/1024:.3f} MB in {diff:.3f}s "
            f"({int(size) / 8 / 1024 / 1024 / diff:.3f} MB/s)"
        )
        return response 