from typing import TypedDict


class ObjectOwnerID(TypedDict):
    owner_id_is_autoset: bool
    owner_id: int


class TagIsPublished(TypedDict):
    is_published: bool
