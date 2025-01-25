from pydantic import BaseModel, ConfigDict, Field
from typing import Literal, Annotated

from backend_main.types.common import PositiveInt, Name, Datetime


ObjectType = Literal["link", "markdown", "to_do_list", "composite"]
AddedTags = Annotated[list[PositiveInt | Name], Field(max_length=100)]
RemovedTagIDs = Annotated[list[PositiveInt], Field(max_length=100)]


class UpsertedObjectAttributesAndTags(BaseModel):
    """
    Attributes and tags of an upserted object, excluding `object_id` and `object_type`.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    object_name: Name
    object_description: str
    owner_id: PositiveInt
    is_published: bool
    display_in_feed: bool
    feed_timestamp: Datetime | None
    show_description: bool

    added_tags: AddedTags
    removed_tag_ids: RemovedTagIDs


class UpsertedObjectAttributes(BaseModel):
    """ Attributes of an object, which is upserted into the database. """
    model_config = ConfigDict(extra="ignore", strict=True)

    object_id: PositiveInt
    object_type: ObjectType
    created_at: Datetime
    modified_at: Datetime
    object_name: Name
    object_description: str
    owner_id: PositiveInt
    is_published: bool
    display_in_feed: bool
    feed_timestamp: Datetime | None
    show_description: bool


class ObjectAttributesAndTags(BaseModel):
    """
    Full set of bbject attributes and current tag IDs, as returned by /objects/view route.
    """
    model_config = ConfigDict(extra="ignore", strict=True)

    object_id: int
    object_type: ObjectType
    created_at: Datetime
    modified_at: Datetime
    object_name: Name
    object_description: str
    owner_id: PositiveInt
    is_published: bool
    display_in_feed: bool
    feed_timestamp: Datetime | None
    show_description: bool
    current_tag_ids: list[PositiveInt]
