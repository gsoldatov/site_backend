"""
    Error handling middleware.
"""
from aiohttp import web
from json.decoder import JSONDecodeError
from jsonschema.exceptions import ValidationError
from psycopg2.errors import UniqueViolation

from backend_main.util.json import error_json
from backend_main.util.validation import RequestValidationException


def _get_uv_msg(e):
    """
    Returns custom message to return in case of a UniqueViolation error.
    """
    uv_field_names = {"tag_name": "tag name", "login": "login", "username": "username"}
    error_text = str(e)
    field_name = "data"
    for fn in uv_field_names:
        if error_text.find(fn) > -1:
            field_name = uv_field_names[fn]
            break
            
    return f"Submitted {field_name} already exists."


@web.middleware
async def error_middleware(request, handler):
    try:
        return await handler(request)
    except JSONDecodeError:
        raise web.HTTPBadRequest(text = error_json("Request body must be a valid JSON document."), content_type = "application/json")
    except ValidationError as e:
        path = "JSON root" if len(e.absolute_path) == 0 else f"""'{"' > '".join(map(str, e.absolute_path))}'"""
        msg = f"JSON validation error at {path}: {e.message}"
        raise web.HTTPBadRequest(text = error_json(msg), content_type = "application/json")
    except RequestValidationException as e:
        raise web.HTTPBadRequest(text = error_json(e), content_type = "application/json")
    except UniqueViolation as e:
            raise web.HTTPBadRequest(text = error_json(_get_uv_msg(e)), content_type = "application/json")
