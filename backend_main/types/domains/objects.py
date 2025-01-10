from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

from backend_main.types.common import PositiveInt, Name, Datetime


# class Tag(BaseModel):
#     """
#     Data class containing attributes of a tag.
#     """
#     model_config = ConfigDict(extra="ignore", strict=True)