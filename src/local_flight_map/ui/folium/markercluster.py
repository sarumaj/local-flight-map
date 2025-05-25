from folium.plugins import MarkerCluster as FoliumMarkerCluster

from .jscode import JsCode, FoliumJsCode


class MarkerCluster(FoliumMarkerCluster):
    """
    MarkerCluster is a class that extends folium.plugins.MarkerCluster.
    It adds a custom icon to the marker cluster.
    """
    def __init__(self, *args, **kwargs):
        options = JsCode.get_options(
            prefix="markercluster_",
            value_class=str,
            value_class_mapping={
                "chunkProgress": FoliumJsCode,
            },
        )
        super().__init__(*args, **{**options, **kwargs})
