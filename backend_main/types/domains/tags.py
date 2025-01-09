from pydantic import BaseModel, ConfigDict, Field

from backend_main.types.common import PositiveInt, Name, Datetime


class Tag(BaseModel):
    """
    Data class containing attributes of a tag.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    tag_id: PositiveInt
    created_at: Datetime
    modified_at: Datetime
    tag_name: Name
    tag_description: str
    is_published: bool


class AddedTag(BaseModel):
    """
    Added tag properties, which are inserted into the database.
    """
    model_config = ConfigDict(extra="ignore", strict=True)

    created_at: Datetime
    modified_at: Datetime
    tag_name: Name
    tag_description: str
    is_published: bool


class TagNameToIDMap(BaseModel):
    """
    Data class, containing a mapping between tag names and IDs.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    map: dict[str, int]
