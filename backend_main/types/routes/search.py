from pydantic import BaseModel, ConfigDict

from backend_main.types.domains.search import SearchQuery, SearchResult


# /search
class SearchRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    query: SearchQuery


class SearchResponseBody(SearchResult):
    pass
