from datetime import datetime
from json.decoder import JSONDecodeError

from aiohttp import web
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from psycopg2.errors import InvalidTextRepresentation, UniqueViolation
from sqlalchemy import select, func

from backend_main.routes.util import row_proxy_to_dict, error_json
from backend_main.schemas.tags import tag_add_schema, tag_update_schema, tag_view_schema


async def add(request):
    try:
        # Validate request data and add missing values
        data = await request.json()
        validate(instance = data, schema = tag_add_schema)
        data.pop("tag_id", None) # use db autogeneration for the primary key
        current_time = datetime.utcnow()
        data["created_at"] = current_time
        data["modified_at"] = current_time
        data["tag_description"] = data.get("tag_description")

        # Add the tag
        async with request.app["engine"].acquire() as conn:
            tags = request.app["tables"]["tags"]      
            result = await conn.execute(tags.insert().\
                returning(tags.c.tag_id, tags.c.created_at, tags.c.modified_at,
                        tags.c.tag_name, tags.c.tag_description).\
                values(data)
                )
            record = await result.fetchone()
            return web.json_response(row_proxy_to_dict(record))
    
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
    tag_id = request.match_info["id"]
    tags = request.app["tables"]["tags"]

    async with request.app["engine"].acquire() as conn:
        # Delete the tag
        try:
            result = await conn.execute(tags.delete().\
                where(tags.c.tag_id == tag_id).\
                returning(tags.c.tag_id)
                
                )
            record = await result.fetchone()
            if not record:
                raise web.HTTPNotFound(text = error_json(f"tag_id '{tag_id}' does not exist."), content_type = "application/json")

            return web.json_response(row_proxy_to_dict(record))
        
        except InvalidTextRepresentation:
            raise web.HTTPNotFound(text = error_json(f"tag_id '{tag_id}' does not exist."), content_type = "application/json")


async def view(request):
    try:
        # Validate request data
        data = await request.json()
        validate(instance = data, schema = tag_view_schema)

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


"""
# Old version with date/name sort and pagination support; replaced a route 
# which returns a list of tags by their ids
async def view(request):
    tags = request.app["tables"]["tags"]

    # Get query parameters
    try:
        first = int(request.query.get("first"))
    except (TypeError, ValueError):
        first = 0
    
    try:
        count = int(request.query.get("count"))
        count = min(max(count, 1), 500)
    except (TypeError, ValueError):
        count = 10
    
    order_by = tags.c.created_at if request.query.get("order_by") == "created_at" else tags.c.tag_name
    asc = False if request.query.get("asc", "true").lower() == "false" else True
    
    # Get tags
    async with request.app["engine"].acquire() as conn:
        result = await conn.execute(select([tags]).\
                    order_by(order_by if asc else order_by.desc()).\
                    limit(count).\
                    offset(first)
                    )
        records = []
        for row in await result.fetchall():
            records.append(row_proxy_to_dict(row))
        
        # Get tag count
        result = await conn.execute(select([func.count()]).select_from(tags))
        total = (await result.fetchone())[0]

        response = {
            "first": first,
            "last": first + count - 1,
            "total": total,
            "tags": records
        }   
        return web.json_response(response)
"""

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
                    web.delete("/delete/{id}", delete, name = "delete"),
                    web.post("/view", view, name = "view"),
                    web.get("/view/all", view_all, name = "view_all"),
                    web.put("/merge", merge, name = "merge"),
                    web.post("/link/{type}", link, name = "link"),
                    web.delete("/unlink/{type}", unlink, name = "unlink"),
                    web.get("/get_linked/{id}", get_linked, name="get_linked")
                ])
    return app
