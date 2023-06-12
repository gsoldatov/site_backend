import asyncio
from functools import partial
from datetime import datetime

from sqlalchemy import select

from backend_main.db_operations.searchables.data_classes import SearchableItem, SearchableCollection
from backend_main.db_operations.searchables.markdown import markdown_batch_to_searchable_collection


async def process_object_batch_coro(request, object_ids):
    """
    Gets objects' attributes & data, processes them and updates `searchables` table for the provided `object_ids`.
    """
    if len(object_ids) == 0: return

    searchables = request.config_dict["tables"]["searchables"]
    conn = request["conn_searchables"]
    modified_at = datetime.utcnow()

    try:
        trans = await conn.begin()

        searchables_data = await _process_objects_coro(request, object_ids)

        if len(searchables_data) > 0:
            await conn.execute(searchables.delete().
                where(searchables.c.object_id.in_(object_ids))
            )

            insert_data = searchables_data.serialize_for_insert("object_id", modified_at)

            await conn.execute(searchables.insert().values(insert_data))

        await trans.commit()
    except Exception:
        await trans.rollback()
        raise


async def _process_objects_coro(request, object_ids):
    """
    Returns searchable text from `objects` table for the provided `object_ids`.
    """
    # Fetch object attributes
    conn = request["conn_searchables"]
    objects = request.config_dict["tables"]["objects"]

    cursor = await conn.execute(
        select([objects.c.object_id, objects.c.object_name, 
                objects.c.object_description, objects.c.object_type])
        .where(objects.c.object_id.in_(object_ids))
    )

    result = SearchableCollection()
    md_batch = []
    types = {"link": [], "markdown": [], "to_do_list": []}

    for r in await cursor.fetchall():
        # Process object names to searchable data
        result.add_item(
            SearchableItem(r["object_id"], text_a=r["object_name"])
        )

        # Prepare object descriptions for parsing
        md_batch.append({"id": r["object_id"], "raw_markdown": r["object_description"]})

        # Add object to the list of specific type
        if r["object_type"] in types: types[r["object_type"]].append(r["object_id"])
    
    # Wrap function to pass arguments into a thread
    job_fn = partial(markdown_batch_to_searchable_collection, md_batch)

    # Process object descriptions and add them to results
    loop = asyncio.get_event_loop()
    result += await loop.run_in_executor(None, job_fn)

    # Process `link` object data
    if len(types["link"]) > 0:
        links = request.config_dict["tables"]["links"]

        cursor = await conn.execute(
            select([links.c.object_id, links.c.link])
            .where(links.c.object_id.in_(types["link"]))
        )

        for r in await cursor.fetchall():
            result.add_item(SearchableItem(r["object_id"], text_b=r["link"]))
    
    # Process `markdown` object data
    if len(types["markdown"]) > 0:
        markdown = request.config_dict["tables"]["markdown"]

        cursor = await conn.execute(
            select([markdown.c.object_id, markdown.c.raw_text])
            .where(markdown.c.object_id.in_(types["markdown"]))
        )

        md_batch = []
        for r in await cursor.fetchall():
            md_batch.append({"id": r["object_id"], "raw_markdown": r["raw_text"]})
        
        job_fn = partial(markdown_batch_to_searchable_collection, md_batch)
        result += await loop.run_in_executor(None, job_fn)
    
    # Process `to_do_list` object data
    if len(types["to_do_list"]) > 0:
        to_do_list_items = request.config_dict["tables"]["to_do_list_items"]

        cursor = await conn.execute(
            select([to_do_list_items.c.object_id, to_do_list_items.c.item_text, to_do_list_items.c.commentary])
            .where(to_do_list_items.c.object_id.in_(types["to_do_list"]))
        )

        for r in await cursor.fetchall():
            result.add_item(SearchableItem(r["object_id"], text_b=r["item_text"], text_c=r["commentary"]))
    
    return result
