"""
Base module for the API package.
Provides base classes and utilities for API clients and data structures.
"""

from typing import Dict, Any, List, Union
from dataclasses import asdict
import orjson as json
from itertools import zip_longest


class ResponseObject:
    """
    Base class for API response objects.
    Provides methods for converting between different data formats.
    """
    __annotations__: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the object to a dictionary.

        Returns:
            A dictionary representation of the object
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResponseObject':
        """
        Create an object from a dictionary.

        Args:
            data: The dictionary to create the object from

        Returns:
            A new ResponseObject instance
        """
        defaults = {}
        for field_name, field_type in cls.__annotations__.items():
            if hasattr(field_type, "__origin__"):
                if field_type.__origin__ is Union:
                    try:
                        defaults[field_name] = field_type.__args__[1]()
                    except Exception:
                        defaults[field_name] = None
                elif field_type.__origin__ is Union:
                    defaults[field_name] = None
        defaults.update(data)
        return cls(**defaults)

    def to_json(self) -> str:
        """
        Convert the object to a JSON string.

        Returns:
            A JSON string representation of the object
        """
        return json.dumps(self.to_dict()).decode("utf-8")

    @classmethod
    def from_json(cls, json_str: str) -> 'ResponseObject':
        """
        Create an object from a JSON string.

        Args:
            json_str: The JSON string to create the object from

        Returns:
            A new ResponseObject instance
        """
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def from_list(cls, data: List[Any]) -> 'ResponseObject':
        """
        Create an object from a list of values.

        Args:
            data: The list of values to create the object from

        Returns:
            A new ResponseObject instance
        """
        return cls.from_dict(dict(zip_longest(cls.__annotations__.keys(), data)))
