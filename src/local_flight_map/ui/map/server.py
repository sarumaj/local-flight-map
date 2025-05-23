import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path


class MapServer:
    """Handles FastAPI server setup and configuration"""

    def __init__(self):
        self._app = fastapi.FastAPI()
        self._setup_middleware()
        self._setup_static_files()

    def _setup_middleware(self):
        """Setup CORS middleware"""
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "HEAD", "OPTIONS"],
            allow_headers=["*"],
        )

    def _setup_static_files(self):
        """Setup static files serving"""
        self._app.mount(
            "/ui/static",
            StaticFiles(directory=str(Path(__file__).parent / "static")),
            name="static"
        )

    @property
    def app(self) -> fastapi.FastAPI:
        """Get the FastAPI application instance"""
        return self._app
