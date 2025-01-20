from pydantic import BaseModel, ConfigDict
from typing import Literal

from backend_main.types.common import PositiveInt, Name, Datetime


ObjectType = Literal["link", "markdown", "to_do_list", "composite"]


class ObjectAttributesAndTags(BaseModel):
    """
    Object attributes and current tag IDs, as returned by /objects/view route.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

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
