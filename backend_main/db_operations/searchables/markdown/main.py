from backend_main.db_operations.searchables.data_classes import SearchableCollection
from backend_main.db_operations.searchables.markdown.util import get_markdown_processor


def markdown_to_searchable_item(text, item_id = None, important_weight = "a", regular_weight = "b"):
    """
    Processes provided `text` string as Markdown and returns searchable text in a `SearchableItem` object.
    `item_id` can be passed to set it in resulting object.
    `important_weight` and `regular_weight` define the search weights for the important & regular text found in Markdown (default to "a" and "b").
    """
    md = get_markdown_processor(item_id, important_weight, regular_weight)

    md.convert(text)

    return md.searchable_item


def markdown_batch_to_searchable_collection(batch, important_weight = "a", regular_weight = "b"):
    """
    Processes a batch of raw Markdown texts into a searchable collection and returns it.

    `batch` - a list of dictionaries with numeric `id` and string `raw_markdown` texts;
    `important_weight` and `regular_weight` define the search weights for the important & regular text found in Markdown (default to "a" and "b").
    """
    result = SearchableCollection()
    for item in batch:
        result.add_item(
            markdown_to_searchable_item(item["raw_markdown"], item_id=item["id"], 
                                        important_weight=important_weight, regular_weight=regular_weight)
        )
    return result
