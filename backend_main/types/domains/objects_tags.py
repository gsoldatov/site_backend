from pydantic import BaseModel, ConfigDict

from backend_main.types.common import PositiveInt


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
