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

from backend_main.schemas.objects import objects_add_schema, objects_update_schema, objects_view_schema, objects_delete_schema

from backend_main.routes.objects_links import add_link, view_link, update_link, delete_link

from backend_main.routes.util import row_proxy_to_dict, error_json, LinkValidationException


async def add(request):
    try:
        # Validate request body
        data = await request.json()
        validate(instance = data, schema = objects_add_schema)
        current_time = datetime.utcnow()
        data["object"]["created_at"] = current_time
        data["object"]["modified_at"] = current_time

        # Insert data in a transaction
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
    except (ValidationError, LinkValidationException) as e:
        raise web.HTTPBadRequest(text = error_json(e), content_type = "application/json")
    except UniqueViolation as e:
            raise web.HTTPBadRequest(text = error_json("Submitted object name already exists."), content_type = "application/json")


async def view(request):
    try:
        # Validate request body
        data = await request.json()
        validate(instance = data, schema = objects_view_schema)

        async with request.app["engine"].acquire() as conn:
            objects = request.app["tables"]["objects"]
            object_ids = data.get("object_ids", [])
            object_data_ids = data.get("object_data_ids", [])
            object_attrs, object_data = [], []

            # Query general attributes for provided object_ids
            if len(object_ids) > 0:
                result = await conn.execute(select([objects.c.object_id, objects.c.object_type, objects.c.created_at,
                                                    objects.c.modified_at, objects.c.object_name, objects.c.object_description]).
                                            where(objects.c.object_id.in_(object_ids))
                )
                for row in await result.fetchall():
                    object_attrs.append(row_proxy_to_dict(row))
            
            # Query object data for provided object_data_ids
            if len(object_data_ids) > 0:
                # Query object types for the requested objects
                result = await conn.execute(select([objects.c.object_type]).
                                            distinct().
                                            where(objects.c.object_id.in_(object_data_ids))
                )
                object_types = []
                for row in await result.fetchall():
                    object_types.append(row["object_type"])
                
                
                # Run handlers for each of the object types
                for object_type in object_types:
                    handler = get_func_name("view", object_type)

                    # handler function must return a list of dict objects with specific object_data attributes
                    object_type_data = await handler(request, conn, object_data_ids)
                    for d in object_type_data:
                        d["object_type"] = object_type
                    object_data.extend(object_type_data)
            
            if len(object_attrs) == 0 and len(object_data) == 0:
                raise web.HTTPNotFound(text = error_json("Objects not found."), content_type = "application/json")

            return web.json_response({ "objects": object_attrs, "object_data": object_data })
    except JSONDecodeError:
        raise web.HTTPBadRequest(text = error_json("Request body must be a valid JSON document."), content_type = "application/json")
    except (ValidationError, LinkValidationException) as e:
        raise web.HTTPBadRequest(text = error_json(e), content_type = "application/json")


async def update(request):
    try:
        # Validate request body
        data = await request.json()
        validate(instance = data, schema = objects_update_schema)
        current_time = datetime.utcnow()
        data["object"]["modified_at"] = current_time

        # Insert general object data
        async with request.app["engine"].acquire() as conn:
            trans = await conn.begin()
            try:
                object_data = data["object"].pop("object_data")

                # Insert general object data
                objects = request.app["tables"]["objects"]
                object_id = data["object"]["object_id"]
                
                result = await conn.execute(objects.update().\
                    where(objects.c.object_id == object_id).\
                    values(data["object"]).\
                    returning(objects.c.object_id, objects.c.object_type, objects.c.created_at, objects.c.modified_at,
                            objects.c.object_name, objects.c.object_description)
                    )
                record = await result.fetchone()
                if not record:
                    await trans.rollback()
                    raise web.HTTPNotFound(text = error_json(f"object_id '{object_id}' not found."), content_type = "application/json")
            
                # Call handler to update object-specific data
                specific_data = {"object_id": record["object_id"], "object_data": object_data}
                handler = get_func_name("update", record["object_type"])
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
    except (ValidationError, LinkValidationException) as e:
        raise web.HTTPBadRequest(text = error_json(e), content_type = "application/json")
    except UniqueViolation as e:
            raise web.HTTPBadRequest(text = error_json("Submitted object name already exists."), content_type = "application/json")


async def delete(request):
    try:
        # Validate request body
        data = await request.json()
        validate(instance = data, schema = objects_delete_schema)

        # Delete objects in a transaction
        async with request.app["engine"].acquire() as conn:
            trans = await conn.begin()
            try:
                # Get object types and call handlers for each type to delete object-specific data
                objects = request.app["tables"]["objects"]
                result = await conn.execute(select([objects.c.object_type]).
                            distinct().
                            where(objects.c.object_id.in_(data["object_ids"]))
                            )
                object_types = []
                for row in await result.fetchall():
                    object_types.append(row["object_type"])

                if len(object_types) == 0:
                    raise web.HTTPNotFound(text = error_json("Objects(s) not found."), content_type = "application/json")

                for object_type in object_types:
                    handler = get_func_name("delete", object_type)
                    await handler(request, conn, data["object_ids"])

                # Delete general data
                result = await conn.execute(objects.delete().\
                            where(objects.c.object_id.in_(data["object_ids"])).\
                            returning(objects.c.object_id)
                            )
                object_ids = []
                for row in await result.fetchall():
                    object_ids.append(row["object_id"])

                # Commit transaction
                await trans.commit()

                # Send response
                response = {"object_ids": object_ids}
                return web.json_response(response)
            except Exception as e:
                # Rollback if an error occurs
                await trans.rollback()
                raise e
        
    except JSONDecodeError:
        raise web.HTTPBadRequest(text = error_json("Request body must be a valid JSON document."), content_type = "application/json")
    except (ValidationError, LinkValidationException) as e:
        raise web.HTTPBadRequest(text = error_json(e), content_type = "application/json")


async def get_page_object_ids(request):
    pass


async def get_object_ids(request):
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
                    web.post("/get_object_ids", get_object_ids, name = "get_object_ids")
                ])
    return app