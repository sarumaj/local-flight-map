from folium import JsCode as FoliumJsCode
from pathlib import Path
from typing import Union


class JsCode(FoliumJsCode):
    """
    JsCode is a class that extends folium.JsCode.

    It loads the js files from the js directory.
    It also provides a method to get the options for the js files.
    """
    js_dir = Path(__file__).parent / "js"

    def __init__(self, script: str):
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
        Get the options for the js files.

        Args:
            prefix: The prefix of the js files.
            value_class: The class of the value.

        Returns:
            A dictionary of the options for the js files,
            with the key being the filename without the prefix and the value being the js code.
        """
        options = {
            key: value_class_mapping.get(key, value_class)(cls(filename.name))
            for filename in cls.js_dir.glob(f"{prefix}*.js")
            for key in (filename.stem[len(prefix):],)
        }
        return options
