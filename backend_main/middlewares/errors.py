"""
    Error handling middleware.
"""
from aiohttp import web
from json.decoder import JSONDecodeError
from jsonschema.exceptions import ValidationError
from psycopg2.errors import UniqueViolation, OperationalError

from backend_main.util.json import error_json
from backend_main.validation.util import RequestValidationException


@web.middleware
async def error_middleware(request, handler):
    try:
        # TODO log request processing end
        return await handler(request)
    except JSONDecodeError:
        # TODO log validation error
        raise web.HTTPBadRequest(text=error_json("Request body must be a valid JSON document."), content_type="application/json")
    except ValidationError as e:
        # TODO log validation error
        path = "JSON root" if len(e.absolute_path) == 0 else f"""'{"' > '".join(map(str, e.absolute_path))}'"""
        msg = f"JSON validation error at {path}: {e.message}"
        raise web.HTTPBadRequest(text = error_json(msg), content_type="application/json")
    except RequestValidationException as e:
        # TODO log validation error
        raise web.HTTPBadRequest(text=error_json(e), content_type="application/json")
    except UniqueViolation as e:
        # TODO log validation error
        raise web.HTTPBadRequest(text=error_json(_get_uv_msg(e)), content_type="application/json")
    except OperationalError as e:
        # TODO log db connection failure
        _raise_500(request, e)
    except web.HTTPException:
        # TODO log aiohttp.web HTTP exceptions (status & response body)
        raise
    except Exception as e:
        # TODO log unexpected error
        _raise_500(request, e)


def _raise_500(request, exception):
    """
    Handles 500 error raising.
    If app is in debug mode, simply raises `exception` to allow aiohttp.server logger to capture error stacktrace.
    Otherwise raises web.HTTPInternalServerError with an overriden text.
    """
    if request.config_dict["config"]["app"]["debug"]:
        raise exception
    else:
        raise web.HTTPInternalServerError(text="Server failed to process request.")


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