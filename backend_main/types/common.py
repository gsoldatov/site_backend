from datetime import datetime
from math import inf
from typing import Annotated, Iterable, cast, Any
from typing_extensions import Self

from pydantic import BaseModel, Field, PlainValidator, PlainSerializer, model_validator


# Numeric
PositiveInt = Annotated[int, Field(ge=1)]
""" Integer > 0. """
NonNegativeInt = Annotated[int, Field(ge=0)]
""" Integer >= 0. """
Port = Annotated[int, Field(ge=1024, le=65535)]
""" A non-system port number. """

# Strings
NonEmptyString = Annotated[str, Field(min_length=1)]
"""String with length > 0."""
Name = Annotated[str, Field(min_length=1, max_length=255)]
"""String with 0 < length < 256."""
QueryText = Name
"""String with 0 < length < 256."""
Password = Annotated[str, Field(min_length=8, max_length=72)]
"""String with 8 <= length = 72."""


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
def validate_datetime(value: Any) -> datetime:
    """
    Custom validator for the `Datetime` type, which allows ISO-formatted strings.
    """
    if isinstance(value, datetime): return value
    elif isinstance(value, str): return datetime.fromisoformat(value)
    else: raise ValueError("Input should be a valid datetime")


Datetime = Annotated[
    datetime,
    # Field(strict=False),    # allow converting from strings 
    #                         # (NOTE: this does not work in type unions with strict mode enabled)
    PlainValidator(validate_datetime),
    PlainSerializer(lambda x: x.isoformat(), when_used="always")
]
"""
`datetime` class with custom JSON serializer.
Can be passed to DB queries.
"""

# Collections
def has_unique_items(it: Iterable):
    """
    Iterable validator, which ensures it has unique items.
    """
    existing = set()
    for element in it:
        if element in existing:
            raise ValueError(f"Element '{element}' is not unique.")
        existing.add(element)
    return it


# Mixins
class AnyOf:
    """
    Mixin class with a model validator, which ensures that at least one field is not null.
    `__any_of_fields__` can be overridden to apply the check to a specific subset of attributes only.
    """
    __any_of_fields__: Iterable[str] | None = None

    @model_validator(mode="after")
    def validator(self) -> Self:
        checked_fields = tuple(
            self.__any_of_fields__
            or cast(BaseModel, self).model_fields.keys()
        )

        for attr in checked_fields:
            if getattr(self, attr, None) is not None:
                return self
        raise ValueError(f"At least one non-null field from {checked_fields} is required.")


class OneOf:
    """
    Mixin class with a model validator, which ensures that exactly one field is not null.
    `__one_of_fields__` can be overridden to apply the check to a specific subset of attributes only.
    """
    __one_of_fields__: Iterable[str] | None = None

    @model_validator(mode="after")
    def validator(self) -> Self:
        checked_fields = tuple(
            self.__one_of_fields__
            or cast(BaseModel, self).model_fields.keys()
        )

        count = 0

        for attr in checked_fields:
            if getattr(self, attr, None) is not None:
                count += 1
        
        if count != 1:
            raise ValueError(f"Exactly one non-null field from {checked_fields} is required.")
        return self
