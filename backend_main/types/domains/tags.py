from pydantic import BaseModel, ConfigDict

from backend_main.types.common import PositiveInt


# class NewTag(BaseModel):
#     """
#     New tag properties, which are inserted into the database.
#     """
#     model_config = ConfigDict(extra="forbid", strict=True)



class TagNameToIDMap(BaseModel):
    """
    Data class, containing a mapping between tag names and IDs.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    map: dict[str, int]
