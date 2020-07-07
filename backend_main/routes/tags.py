from datetime import datetime
from json.decoder import JSONDecodeError

from aiohttp import web
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from psycopg2.errors import InvalidTextRepresentation, UniqueViolation
from sqlalchemy import select, func

from backend_main.routes.util import row_proxy_to_dict, error_json
from backend_main.schemas.tags import tag_add_schema, tag_update_schema, tag_view_delete_schema, tag_get_page_tag_ids_schema


async def add(request):
    try:
        # Validate request data and add missing values
        data = await request.json()
        validate(instance = data, schema = tag_add_schema)
        current_time = datetime.utcnow()
        data["tag"]["created_at"] = current_time
        data["tag"]["modified_at"] = current_time

        # Add the tag
        async with request.app["engine"].acquire() as conn:
            tags = request.app["tables"]["tags"]      
            result = await conn.execute(tags.insert().\
                returning(tags.c.tag_id, tags.c.created_at, tags.c.modified_at,
                        tags.c.tag_name, tags.c.tag_description).\
                values(data["tag"])
                )
            record = await result.fetchone()
            return web.json_response({"tag": row_proxy_to_dict(record)})
    
    except JSONDecodeError:
        raise web.HTTPBadRequest(text = error_json("Request body must be a valid JSON document."), content_type = "application/json")
    except ValidationError as e:
        raise web.HTTPBadRequest(text = error_json(e), content_type = "application/json")
    except UniqueViolation as e:
            raise web.HTTPBadRequest(text = error_json("Submitted tag name already exists."), content_type = "application/json")


async def update(request):
    try:
        # Validate request data and add missing values
        data = await request.json()
        validate(instance = data, schema = tag_update_schema)
        data["tag"]["modified_at"] = datetime.utcnow()

        # Update the tag
        async with request.app["engine"].acquire() as conn:
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

            return web.json_response({"tag": row_proxy_to_dict(record)})
    
    except JSONDecodeError:
        raise web.HTTPBadRequest(text = error_json("Request body must be a valid JSON document."), content_type = "application/json")
    except ValidationError as e:
        raise web.HTTPBadRequest(text = error_json(e), content_type = "application/json")
    except UniqueViolation as e:
        raise web.HTTPBadRequest(text = error_json(f"Submitted tag name already exists."), content_type = "application/json")


async def delete(request):
    try:
        # Validate request data and add missing values
        data = await request.json()
        validate(instance = data, schema = tag_view_delete_schema)

        # Delete tags
        async with request.app["engine"].acquire() as conn:
            tags = request.app["tables"]["tags"]

            result = await conn.execute(tags.delete().\
                        where(tags.c.tag_id.in_(data["tag_ids"])).\
                        returning(tags.c.tag_id)
                        )
            tag_ids = []
            for row in await result.fetchall():
                tag_ids.append(row["tag_id"])
            
            if len(tag_ids) == 0:
                raise web.HTTPNotFound(text = error_json("Tag(s) not found."), content_type = "application/json")
            
            response = {"tag_ids": tag_ids}
            return web.json_response(response)
    except JSONDecodeError:
        raise web.HTTPBadRequest(text = error_json("Request body must be a valid JSON document."), content_type = "application/json")
    except ValidationError as e:
        raise web.HTTPBadRequest(text = error_json(e), content_type = "application/json")


async def view(request):
    try:
        # Validate request data
        data = await request.json()
        validate(instance = data, schema = tag_view_delete_schema)

        # Query tags
        async with request.app["engine"].acquire() as conn:
            tags = request.app["tables"]["tags"]

            result = await conn.execute(select([tags]).\
                        where(tags.c.tag_id.in_(data["tag_ids"]))
                        )
            records = []
            for row in await result.fetchall():
                records.append(row_proxy_to_dict(row))
            
            if len(records) == 0:
                raise web.HTTPNotFound(text = error_json("Requested tags not found."), content_type = "application/json")
            
            response = {"tags": records}
            return web.json_response(response)
    
    except JSONDecodeError:
        raise web.HTTPBadRequest(text = error_json("Request body must be a valid JSON document."), content_type = "application/json")
    except ValidationError as e:
        raise web.HTTPBadRequest(text = error_json(e), content_type = "application/json")


async def get_page_tag_ids(request):
    try:
        # Validate request data
        data = await request.json()
        validate(instance = data, schema = tag_get_page_tag_ids_schema)        
        
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
        
    except JSONDecodeError:
        raise web.HTTPBadRequest(text = error_json("Request body must be a valid JSON document."), content_type = "application/json")
    except ValidationError as e:
        raise web.HTTPBadRequest(text = error_json(e), content_type = "application/json")


async def view_all(request):
    pass


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
                    web.get("/view/all", view_all, name = "view_all"),
                    web.put("/merge", merge, name = "merge"),
                    web.post("/link/{type}", link, name = "link"),
                    web.delete("/unlink/{type}", unlink, name = "unlink"),
                    web.get("/get_linked/{id}", get_linked, name="get_linked")
                ])
    return app
