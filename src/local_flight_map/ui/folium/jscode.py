"""
JavaScript code module for the Local Flight Map application.
Provides utilities for loading and managing JavaScript code in the map interface.
"""

from folium import JsCode as FoliumJsCode
from pathlib import Path
from typing import Union


class JsCode(FoliumJsCode):
    """
    Extended JavaScript code class for the Local Flight Map application.
    Loads JavaScript files from the js directory and provides utilities for managing them.

    This class extends folium.JsCode to add functionality for loading JavaScript files
    from a specific directory and managing their options.

    Attributes:
        js_dir: The directory containing JavaScript files.
    """
    js_dir = Path(__file__).parent / "js"

    def __init__(self, script: str):
        """
        Initialize a new JavaScript code instance.

        Args:
            script: The name of the JavaScript file to load.

        Raises:
            FileNotFoundError: If the specified JavaScript file does not exist.
        """
        self._path = self.js_dir / script
        if not self._path.exists():
            raise FileNotFoundError(f"File {self._path} not found")
        FoliumJsCode.__init__(self, self._path.read_text())

    @classmethod
    def get_options(
        cls, *,
        prefix: str,
        value_class: Union[str, "FoliumJsCode"] = FoliumJsCode,
        value_class_mapping: dict[str, Union[str, "FoliumJsCode"]] = {},
    ) -> Union[dict[str, "FoliumJsCode"], dict[str, str]]:
        """
        Get options for JavaScript files with a specific prefix.

        Args:
            prefix: The prefix of the JavaScript files to load.
            value_class: The class to use for values in the options dictionary.
            value_class_mapping: A dictionary mapping specific keys to custom value classes.

        Returns:
            A dictionary where:
            - Keys are the filenames without the prefix
            - Values are either:
              - Instances of value_class containing the JavaScript code
              - Custom values specified in value_class_mapping

        Example:
            >>> JsCode.get_options(prefix="realtime_")
            {
                "source": <FoliumJsCode instance>,
                "get_feature_id": <FoliumJsCode instance>,
                ...
            }
        """
        options = {
            key: value_class_mapping.get(key, value_class)(cls(filename.name))
            for filename in cls.js_dir.glob(f"{prefix}*.js")
            for key in (filename.stem[len(prefix):],)
        }
        return options
