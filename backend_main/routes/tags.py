from datetime import datetime

from aiohttp import web
from jsonschema import validate
from sqlalchemy import select, func

from backend_main.db_operaions.objects_tags import update_objects_tags
from backend_main.schemas.tags import tags_add_schema, tags_update_schema, tags_view_delete_schema, \
    tags_get_page_tag_ids_schema, tags_search_schema
from backend_main.util.json import row_proxy_to_dict, error_json


async def add(request):
    # Validate request data and add missing values
    data = await request.json()
    validate(instance = data, schema = tags_add_schema)
    current_time = datetime.utcnow()
    data["tag"]["created_at"] = current_time
    data["tag"]["modified_at"] = current_time
    added_object_ids = data["tag"].pop("added_object_ids", [])

    # Insert data in a transaction
    async with request.app["engine"].acquire() as conn:
        trans = await conn.begin()
        try:
            # Add the tag
            tags = request.app["tables"]["tags"]      
            result = await conn.execute(tags.insert().\
                returning(tags.c.tag_id, tags.c.created_at, tags.c.modified_at,
                        tags.c.tag_name, tags.c.tag_description).\
                values(data["tag"])
                )
            tag = row_proxy_to_dict(await result.fetchone())

            # Tag objects with the new tag
            tag["object_updates"] = await update_objects_tags(request, conn, {"tag_ids": [tag["tag_id"]], "added_object_ids": added_object_ids})
            
            # Commit transaction
            await trans.commit()

            return web.json_response({"tag": tag})
        except Exception as e:
            # Rollback if an error occurs
            await trans.rollback()
            raise e


async def update(request):
    # Validate request data and add missing values
    data = await request.json()
    validate(instance = data, schema = tags_update_schema)
    data["tag"]["modified_at"] = datetime.utcnow()
    added_object_ids = data["tag"].pop("added_object_ids", [])
    removed_object_ids = data["tag"].pop("removed_object_ids", [])

    # Insert data in a transaction
    async with request.app["engine"].acquire() as conn:
        trans = await conn.begin()
        try:
            # Update the tag
            tags = request.app["tables"]["tags"]
            tag_id = data["tag"]["tag_id"]

            result = await conn.execute(tags.update().\
                where(tags.c.tag_id == tag_id).\
                values(data["tag"]).\
                returning(tags.c.tag_id, tags.c.created_at, tags.c.modified_at,
                        tags.c.tag_name, tags.c.tag_description)
                )
            
            record = await result.fetchone()
            if not record:
                raise web.HTTPNotFound(text = error_json(f"tag_id '{tag_id}' not found."), content_type = "application/json")
            tag = row_proxy_to_dict(record)

            # Update object's tags
            tag["object_updates"] = await update_objects_tags(request, conn, 
                {"tag_ids": [tag_id], "added_object_ids": added_object_ids, "removed_object_ids": removed_object_ids})

            # Commit transaction
            await trans.commit()

            return web.json_response({"tag": tag})
        except Exception as e:
            # Rollback if an error occurs
            await trans.rollback()
            raise e


async def delete(request):
    # Validate request data and add missing values
    data = await request.json()
    validate(instance = data, schema = tags_view_delete_schema)

    # Delete tags in a transaction
    async with request.app["engine"].acquire() as conn:
        trans = await conn.begin()
        tag_ids = data["tag_ids"]
        try:
            # Remove objects' tags
            await update_objects_tags(request, conn, {"tag_ids": tag_ids, "remove_all_objects": True})

            # Delete the tags
            tags = request.app["tables"]["tags"]
            result = await conn.execute(tags.delete().\
                        where(tags.c.tag_id.in_(tag_ids)).\
                        returning(tags.c.tag_id)
                        )
            tag_ids = []
            for row in await result.fetchall():
                tag_ids.append(row["tag_id"])
            
            if len(tag_ids) == 0:
                raise web.HTTPNotFound(text = error_json("Tag(s) not found."), content_type = "application/json")
            
            # Commit transaction
            await trans.commit()
            
            # Send response
            response = {"tag_ids": tag_ids}
            return web.json_response(response)
        except Exception as e:
            # Rollback if an error occurs
            await trans.rollback()
            raise e


async def view(request):
    # Validate request data
    data = await request.json()
    validate(instance = data, schema = tags_view_delete_schema)
    tags = request.app["tables"]["tags"]
    objects_tags = request.app["tables"]["objects_tags"]
    tag_ids = data["tag_ids"]
    return_current_object_ids = data.get("return_current_object_ids", False)

    # Query tags and tagged objects
    async with request.app["engine"].acquire() as conn:
        # Tags
        result = await conn.execute(select([tags]).\
                    where(tags.c.tag_id.in_(tag_ids))
                    )
        tags = {}
        for row in await result.fetchall():
            tags[row["tag_id"]] = row_proxy_to_dict(row)
            tags[row["tag_id"]]["current_object_ids"] = []
        
        if len(tags) == 0:
            raise web.HTTPNotFound(text = error_json("Requested tags not found."), content_type = "application/json")

        # Tagged objects
        if return_current_object_ids:
            current_tags = await conn.execute(select([objects_tags.c.object_id, objects_tags.c.tag_id])
                                            .where(objects_tags.c.tag_id.in_(tag_ids))
            )            
            for row in await current_tags.fetchall():
                tags[row["tag_id"]]["current_object_ids"].append(row["object_id"])
        
        response = {"tags": [tags[k] for k in tags]}
        return web.json_response(response)


async def get_page_tag_ids(request):
    # Validate request data
    data = await request.json()
    validate(instance = data, schema = tags_get_page_tag_ids_schema)
    
    async with request.app["engine"].acquire() as conn:
        # Set query params
        tags = request.app["tables"]["tags"]
        p = data["pagination_info"]
        order_by = tags.c.modified_at if p["order_by"] == "modified_at" else tags.c.tag_name
        order_asc = p["sort_order"] == "asc"
        items_per_page = p["items_per_page"]
        first = (p["page"] - 1) * items_per_page
        # filter_text = f"%{p['filter_text']}%"
        filter_text = f"%{p['filter_text'].lower()}%"

        # Get tag ids
        result = await conn.execute(select([tags.c.tag_id]).\
                # where(tags.c.tag_name.like(filter_text)).\
                where(func.lower(tags.c.tag_name).like(filter_text)).\
                order_by(order_by if order_asc else order_by.desc()).\
                limit(items_per_page).\
                offset(first)
                )
        tag_ids = []
        for row in await result.fetchall():
            tag_ids.append(row["tag_id"])
        
        if len(tag_ids) == 0:
            raise web.HTTPNotFound(text = error_json("No tags found."), content_type = "application/json")

        # Get tag count
        result = await conn.execute(select([func.count()]).select_from(tags).where(tags.c.tag_name.like(filter_text)))
        total_items = (await result.fetchone())[0]

        response = {
            "page": p["page"],
            "items_per_page": items_per_page,
            "total_items": total_items,
            "order_by": p["order_by"],
            "sort_order": p["sort_order"],
            "filter_text": p["filter_text"],
            "tag_ids": tag_ids
        }
        return web.json_response(response)
        


async def search(request):
    # Validate request data
    data = await request.json()
    validate(instance = data, schema = tags_search_schema)

    async with request.app["engine"].acquire() as conn:
        # Set query params
        tags = request.app["tables"]["tags"]
        query_text = "%" + data["query"]["query_text"] + "%"
        maximum_values = data["query"].get("maximum_values", 10)

        # Get tag ids
        result = await conn.execute(select([tags.c.tag_id])
                                    .where(func.lower(tags.c.tag_name).like(query_text))
                                    .limit(maximum_values)
        )
        tag_ids = []
        for row in await result.fetchall():
            tag_ids.append(row["tag_id"])
        
        if len(tag_ids) == 0:
            raise web.HTTPNotFound(text = error_json("No tags found."), content_type = "application/json")

        return web.json_response({"tag_ids": tag_ids})


async def merge(request):
    pass


async def link(request):
    pass


async def unlink(request):
    pass


async def get_linked(request):
    pass


def get_subapp():
    app = web.Application()
    app.add_routes([
                    web.post("/add", add, name = "add"),
                    web.put("/update", update, name = "update"),
                    web.delete("/delete", delete, name = "delete"),
                    web.post("/view", view, name = "view"),
                    web.post("/get_page_tag_ids", get_page_tag_ids, name = "get_page_tag_ids"),
                    web.post("/search", search, name = "search"),
                    web.put("/merge", merge, name = "merge"),
                    web.post("/link/{type}", link, name = "link"),
                    web.delete("/unlink/{type}", unlink, name = "unlink"),
                    web.get("/get_linked/{id}", get_linked, name="get_linked")
                ])
    return app
