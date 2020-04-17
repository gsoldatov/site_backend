from aiohttp import web
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from psycopg2.errors import UniqueViolation
from datetime import datetime

import os, sys
sys.path.insert(0, os.path.join(sys.path[0], '..'))
from schemas.tags import tag_add_schema, tag_update_schema
from .util import row_proxy_to_dict, error_json, check_if_tag_id_exists


async def add(request):
    data = await request.json()
    try:
        validate(instance = data, schema = tag_add_schema)
    except ValidationError as e:
        raise web.HTTPBadRequest(text = error_json(e), content_type = "application/json")

    async with request.app["engine"].acquire() as conn:
        data.pop("tag_id", None) # use db autogeneration for the primary key
        data["created_at"] = datetime.utcnow()
        data["tag_description"] = data.get("tag_description")
        tags = request.app["tables"]["tags"]

        try:        
            result = await conn.execute(tags.insert().\
                returning(tags.c.tag_id, tags.c.created_at,
                        tags.c.tag_name, tags.c.tag_description).\
                values(data)
                )
            record = await result.fetchone()
            return web.json_response(row_proxy_to_dict(record))
        except UniqueViolation as e:
            raise web.HTTPBadRequest(text = error_json("Submitted tag name already exists."), content_type = "application/json")


async def update(request):
    # Check if tag_id exists
    tag_id = request.match_info["id"]
    if not await check_if_tag_id_exists(request, tag_id):
        raise web.HTTPNotFound(text = error_json(f"tag_id '{tag_id}' does not exist."), content_type = "application/json")
    
    async with request.app["engine"].acquire() as conn:
        tags = request.app["tables"]["tags"]

        # Validate request data
        data = await request.json()
        try:
            validate(instance = data, schema = tag_update_schema)
        except ValidationError as e:
            raise web.HTTPBadRequest(text = error_json(e), content_type = "application/json")

        # Update the tag
        data["tag_name"] = data.get("tag_name")
        data["tag_description"] = data.get("tag_description")
        try:
            result = await conn.execute(tags.update().\
                where(tags.c.tag_id == tag_id).\
                values(data).\
                returning(tags.c.tag_id, tags.c.created_at,
                        tags.c.tag_name, tags.c.tag_description)
                
                )
            record = await result.fetchone()
            return web.json_response(row_proxy_to_dict(record))
        except UniqueViolation as e:
            raise web.HTTPBadRequest(text = error_json(f"tag_name \'{data['tag_name']}\' already exists."), content_type = "application/json")


async def delete(request):
    # Check if tag_id exists
    tag_id = request.match_info["id"]
    if not await check_if_tag_id_exists(request, tag_id):
        raise web.HTTPNotFound(text = error_json(f"tag_id '{tag_id}' does not exist."), content_type = "application/json")

    async with request.app["engine"].acquire() as conn:
        tags = request.app["tables"]["tags"]

        # Delete the tag
        result = await conn.execute(tags.delete().\
            where(tags.c.tag_id == tag_id).\
            returning(tags.c.tag_id)
            
            )
        record = await result.fetchone()
        return web.json_response(row_proxy_to_dict(record))


async def view(request):
    pass


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
                    web.put("/update/{id}", update, name = "update"),
                    web.delete("/delete/{id}", delete, name = "delete"),
                    web.get("/view", view, name = "view"),
                    web.get("/view/all", view_all, name = "view_all"),
                    web.put("/merge", merge, name = "merge"),
                    web.post("/link/{type}", link, name = "link"),
                    web.delete("/unlink/{type}", unlink, name = "unlink"),
                    web.get("/get_linked/{id}", get_linked, name="get_linked")
                ])
    return app
