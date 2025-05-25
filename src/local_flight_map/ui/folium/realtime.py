"""
Real-time data module for the Local Flight Map application.
Provides a custom real-time data implementation for updating aircraft positions on the map.
"""

from folium.plugins import Realtime as FoliumRealtime

from .jscode import JsCode


class Realtime(FoliumRealtime):
    """
    Custom real-time data implementation for the Local Flight Map application.
    Extends folium.plugins.Realtime to add custom behavior for aircraft position updates.

    This class provides real-time updates of aircraft positions on the map,
    with custom behavior for:
    - Data source configuration
    - Feature ID generation
    - Position updates
    - Marker styling
    - Update frequency control
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize a new real-time data instance.

        Args:
            *args: Positional arguments passed to the parent class.
            **kwargs: Keyword arguments passed to the parent class.
                     These will override any default options.

        Note:
            The real-time functionality is configured with custom options loaded from
            JavaScript files with the 'realtime_' prefix. These options control various
            aspects of the real-time updates, including data source configuration,
            update frequency, and marker behavior.
        """
        options = JsCode.get_options(prefix="realtime_")
        FoliumRealtime.__init__(self, *args, **{**options, **kwargs})
