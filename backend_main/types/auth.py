from typing import TypedDict, Protocol


class ObjectOwnerID(TypedDict):
    owner_id_is_autoset: bool
    owner_id: int


class TagIsPublished(Protocol):
    """
    Interface representing tag data including `is_published` attribute.
    """
    is_published: bool
