from datetime import datetime
from math import inf
from typing import Annotated

from pydantic import Field, PlainSerializer


# Numeric
PositiveInt = Annotated[int, Field(ge=1)]
""" Integer > 0. """
Port = Annotated[int, Field(ge=1024, le=65535)]
""" A non-system port number. """

# Strings
NonEmptyString = Annotated[str, Field(min_length=1)]
"""String object with length > 0."""
Name = Annotated[str, Field(min_length=1, max_length=255)]
"""String object with 0 < length < 256."""
Password = Annotated[str, Field(min_length=8, max_length=72)]
"""String object with 8 <= length = 72."""


class HiddenString:
    """
    Validates `value` to be a string with the length between `min_length` and `max_length`.
    Protects `value` from being printed by returning `replacement_string` instead of it.
    """
    def __init__(self, value: str, replacement_string: str = "***", min_length: int = 0, max_length: float | int = inf):
        if not isinstance(value, str):
            raise ValueError("Input should be a valid string")

        if len(value) < min_length:
            c = "character" if min_length == 1 else "characters"
            raise ValueError(f"String should have at least {min_length} {c}")

        if len(value) > max_length:
            c = "character" if max_length == 1 else "characters"
            raise ValueError(f"String should have at most {max_length} {c}")
        
        self.value = value
        self._replacement_string = replacement_string
    
    def __repr__(self):
        return self._replacement_string
    
    def __str__(self):
        return self._replacement_string


# Datetime
Datetime = Annotated[datetime, PlainSerializer(
    lambda x: x.isoformat(), when_used="always"
)]
"""
`datetime` class with custom JSON serializer.
Can be passed to DB queries.
"""
