from folium.plugins import Realtime as FoliumRealtime

from .jscode import JsCode


class Realtime(FoliumRealtime):
    """
    Realtime is a class that extends folium.plugins.Realtime.
    It adds a custom icon to the marker cluster.
    """
    def __init__(self, *args, **kwargs):
        options = JsCode.get_options(prefix="realtime_")
        FoliumRealtime.__init__(self, *args, **{**options, **kwargs})
