import asyncio
from functools import partial
from datetime import datetime

from sqlalchemy import select

from backend_main.db_operations.searchables.data_classes import SearchableItem, SearchableCollection
from backend_main.db_operations.searchables.markdown import markdown_batch_to_searchable_collection


async def process_tag_batch_coro(request, tag_ids):
    """
    Gets tags' attributes, processes them and updates `searchables` table for the provided `tag_ids`.
    """
    if len(tag_ids) == 0: return

    searchables = request.config_dict["tables"]["searchables"]
    conn = request["conn_searchables"]
    modified_at = datetime.utcnow()

    try:
        trans = await conn.begin()

        searchables_data = await _process_tags_coro(request, tag_ids)

        if len(searchables_data) > 0:
            await conn.execute(searchables.delete().
                where(searchables.c.tag_id.in_(tag_ids))
            )

            insert_data = searchables_data.serialize_for_insert("tag_id", modified_at)

            await conn.execute(searchables.insert().values(insert_data))

        await trans.commit()
    except Exception:
        await trans.rollback()
        raise


async def _process_tags_coro(request, tag_ids):
    """
    Returns searchable text from `tags` table for the provided `tag_ids`.
    """
    # Fetch tag attributes
    tags = request.config_dict["tables"]["tags"]

    cursor = await request["conn_searchables"].execute(
        select([tags.c.tag_id, tags.c.tag_name, tags.c.tag_description])
        .where(tags.c.tag_id.in_(tag_ids))
    )

    result = SearchableCollection()
    md_batch = []

    for r in await cursor.fetchall():
        # Process tag names to searchable data
        result.add_item(
            SearchableItem(r["tag_id"], text_a=r["tag_name"])
        )

        # Prepare tag descriptions for parsing
        md_batch.append({"id": r["tag_id"], "raw_markdown": r["tag_description"]})
    
    # Wrap function to pass arguments into a thread
    job_fn = partial(markdown_batch_to_searchable_collection, md_batch)

    # Process tag descriptions and add them to results
    loop = asyncio.get_event_loop()
    result += await loop.run_in_executor(None, job_fn)

    return result
