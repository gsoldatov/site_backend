from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

from backend_main.types.common import QueryText, PositiveInt


class SearchQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    
    query_text: QueryText
    page: int = Field(ge=1)
    items_per_page: int = Field(ge=1)


class _SearchResultItem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    item_type: Literal["object", "tag"]
    item_id: PositiveInt


class SearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    query_text: QueryText
    page: int = Field(ge=1)
    items_per_page: int = Field(ge=1)
    items: list[_SearchResultItem]
    total_items: int
