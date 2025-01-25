from pydantic import BaseModel, ConfigDict
from typing import Any

from backend_main.types.common import PositiveInt
from backend_main.types.domains.objects.attributes import AddedTags, RemovedTagIDs


class ObjectTag(BaseModel):
    """ Object an tag IDs pair. """
    model_config = ConfigDict(extra="ignore", strict=True)

    object_id: PositiveInt
    tag_id: PositiveInt

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, type(self)):
            return self.object_id == other.object_id and self.tag_id == other.tag_id
        return False
    
    def __repr__(self) -> str:
        return str(self)
    
    def __str__(self) -> str:
        return f"{(self.object_id, self.tag_id)}"
    
    def __hash__(self) -> int:
        return hash((self.object_id, self.tag_id))


class ObjectIDAndAddedTags(BaseModel):
    """ `object_id` and `added_tags` attributes from an upserted object. """
    model_config = ConfigDict(extra="ignore", strict=True)

    object_id: PositiveInt
    added_tags: AddedTags


class ObjectIDAndRemovedTagIDs(BaseModel):
    """ `object_id` and `removed_tag_ids` attributes from an upserted object. """
    model_config = ConfigDict(extra="ignore", strict=True)

    object_id: PositiveInt
    removed_tag_ids: RemovedTagIDs


class ObjectsTagsLists(BaseModel):
    """
    Data class with lists of object & tag IDs, combinations of which 
    were added or deleted to the `objects_tags` table.
    """
    model_config = ConfigDict(extra="forbid", strict=True)
    
    object_ids: list[PositiveInt]
    tag_ids: list[PositiveInt]


class ObjectsTagsMap(BaseModel):
    """
    Data class, containing a mapping between object IDs
    and a list of current tag IDs (or vice versa).
    """
    model_config = ConfigDict(extra="forbid", strict=True)
    
    map: dict[int, list[int]]
