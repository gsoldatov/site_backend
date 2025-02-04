def get_search_request_body(
    query_text: str = "word",
    page: int = 1,
    items_per_page: int = 100
):
    """ Returns /search request body with default or custom values. """
    return {
        "query": {
            "query_text": query_text,
            "page": page,
            "items_per_page": items_per_page
        }
    }
