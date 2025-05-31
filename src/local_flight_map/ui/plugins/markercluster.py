"""
Marker cluster module for the Local Flight Map application.
Provides a custom marker cluster implementation for grouping aircraft markers on the map.
"""

from folium.plugins import MarkerCluster as FoliumMarkerCluster

from .jscode import JsCode, FoliumJsCode


class MarkerCluster(FoliumMarkerCluster):
    """
    Custom marker cluster implementation for the Local Flight Map application.
    Extends folium.plugins.MarkerCluster to add custom styling and behavior.

    This class provides a marker cluster that groups nearby aircraft markers
    into clusters, with custom icons and behavior for better visualization.

    The cluster uses custom JavaScript code for:
    - Custom cluster icons
    - Chunk progress tracking
    - Cluster behavior customization
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize a new marker cluster instance.

        Args:
            *args: Positional arguments passed to the parent class.
            **kwargs: Keyword arguments passed to the parent class.
                     These will override any default options.

        Note:
            The cluster is configured with custom options loaded from JavaScript files
            with the 'markercluster_' prefix. The 'chunkProgress' option is specifically
            handled as a FoliumJsCode instance.
        """
        options = JsCode.get_options(
            prefix="markercluster_",
            value_class=str,
            value_class_mapping={
                "chunkProgress": FoliumJsCode,
            },
        )
        FoliumMarkerCluster.__init__(self, *args, **{**options, **kwargs})
