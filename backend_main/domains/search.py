from backend_main.db_operations.search import get_search_results as _get_search_results

from backend_main.types.domains.search import SearchQuery, SearchResult
from backend_main.types.request import Request


async def get_search_results(request: Request, query: SearchQuery) -> SearchResult:
    return await _get_search_results(request, query)
