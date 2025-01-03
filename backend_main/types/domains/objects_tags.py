from pydantic import BaseModel, ConfigDict


class ObjectsTagsMap(BaseModel):
    """
    Data class, containing a mapping between object IDs
    and a list of current tag IDs (or vice versa).
    """
    model_config = ConfigDict(extra="forbid", strict=True)
    
    map: dict[int, list[int]]
