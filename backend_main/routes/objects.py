"""
    Object routes.
"""
from datetime import datetime
from json.decoder import JSONDecodeError

from aiohttp import web
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from psycopg2.errors import UniqueViolation
from sqlalchemy import select

from backend_main.schemas.objects import objects_add_schema, objects_view_delete_schema

from backend_main.routes.objects_links import add as add_link

from backend_main.routes.util import row_proxy_to_dict, objects_row_proxy_to_dict, error_json, URLValidationException


async def add(request):
    try:
        # Validate genaral structure of the request
        data = await request.json()
        validate(instance = data, schema = objects_add_schema)
        current_time = datetime.utcnow()
        data["object"]["created_at"] = current_time
        data["object"]["modified_at"] = current_time

        # Call handler for the provided object type and send the response
        async with request.app["engine"].acquire() as conn:
            trans = await conn.begin()
            try:
                object_data = data["object"].pop("object_data")

                # Insert general object data
                objects = request.app["tables"]["objects"]
                
                result = await conn.execute(objects.insert().\
                    returning(objects.c.object_id, objects.c.object_type, objects.c.created_at, objects.c.modified_at,
                            objects.c.object_name, objects.c.object_description).\
                    values(data["object"])
                    )
                record = await result.fetchone()
            
                # Call handler to add object-specific data
                specific_data = {"object_id": record["object_id"], "object_data": object_data}
                handler = get_func_name("add", data["object"]["object_type"])
                await handler(request, conn, specific_data)
                
                # Commit transaction
                await trans.commit()

                # Send response with object's general data; object-specific data is kept on the frontend and displayed after receiving the response or retrived via object
                return web.json_response({"object": row_proxy_to_dict(record)})
            except Exception as e:
                # Rollback if an error occurs
                await trans.rollback()
                raise e

    except JSONDecodeError:
        raise web.HTTPBadRequest(text = error_json("Request body must be a valid JSON document."), content_type = "application/json")
    except (ValidationError, URLValidationException) as e:
        raise web.HTTPBadRequest(text = error_json(e), content_type = "application/json")
    except UniqueViolation as e:
            raise web.HTTPBadRequest(text = error_json("Submitted object name already exists."), content_type = "application/json")


async def view(request):
    try:
        # Validate genaral structure of the request
        data = await request.json()
        validate(instance = data, schema = objects_view_delete_schema)

        # Query objects
        async with request.app["engine"].acquire() as conn:
            objects = request.app["tables"]["objects"] 
            urls = request.app["tables"]["urls"]

            joined_tables = objects.join(urls, objects.c.object_id == urls.c.object_id, True)

            result = await conn.execute(select([objects, urls.c.link]).\
                        select_from(joined_tables).\
                        where(objects.c.object_id.in_(data["object_ids"]))
                    )
            
            records = []
            for row in await result.fetchall():
                records.append(objects_row_proxy_to_dict(row))
            
            if len(records) == 0:
                raise web.HTTPNotFound(text = error_json("Objects not found."), content_type = "application/json")

            response = {"objects": records}
            return web.json_response(response)

    except JSONDecodeError:
        raise web.HTTPBadRequest(text = error_json("Request body must be a valid JSON document."), content_type = "application/json")
    except (ValidationError, URLValidationException) as e:
        raise web.HTTPBadRequest(text = error_json(e), content_type = "application/json")


async def update(request):
    pass


async def delete(request):
    pass


async def get_page_object_ids(request):
    pass


async def get_tag_ids(request):
    pass


def get_func_name(route, object_type):
    return globals()[f"{route}_{object_type}"]


def get_subapp():
    app = web.Application()
    app.add_routes([
                    web.post("/add", add, name = "add"),
                    web.put("/update", update, name = "update"),
                    web.delete("/delete", delete, name = "delete"),
                    web.post("/view", view, name = "view"),
                    web.post("/get_page_object_ids", get_page_object_ids, name = "get_page_object_ids"),
                    web.post("/get_tag_ids", get_tag_ids, name = "get_tag_ids")
                ])
    return app