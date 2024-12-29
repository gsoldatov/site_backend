from collections.abc import Sequence

from backend_main.db_operations.searchables.markdown.util import get_markdown_processor
from backend_main.db_operations.searchables.types import SearchableCollection, SearchableItem, \
    MarkdownProcessingItem, TextWeight


def markdown_to_searchable_item(
        text: str,
        item_id: int | None = None,
        important_weight: TextWeight = "a",
        regular_weight: TextWeight = "b"
    ) -> SearchableItem:
    """
    Processes provided `text` string as Markdown and returns searchable text in a `SearchableItem` object.
    `item_id` can be passed to set it in resulting object.
    `important_weight` and `regular_weight` define the search weights for the important & regular text found in Markdown (default to "a" and "b").
    """
    md = get_markdown_processor(item_id, important_weight, regular_weight)

    md.convert(text)

    return md.searchable_item


def markdown_batch_to_searchable_collection(
        batch: Sequence[MarkdownProcessingItem],
        important_weight: TextWeight = "a",
        regular_weight: TextWeight = "b"
    ) -> SearchableCollection:
    """
    Processes a batch of raw Markdown texts into a searchable collection and returns it.

    `batch` - a list of dictionaries with numeric `id` and string `raw_markdown` texts;
    `important_weight` and `regular_weight` define the search weights for the important & regular 
        text found in Markdown (default to "a" and "b").
    """
    result = SearchableCollection()
    for item in batch:
        result.add_item(
            markdown_to_searchable_item(
                text=item.raw_markdown,
                item_id=item.id,
                important_weight=important_weight,
                regular_weight=regular_weight
        ))
    return result
