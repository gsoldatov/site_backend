"""
    Error handling middleware.
"""
from aiohttp import web
from json.decoder import JSONDecodeError
from jsonschema.exceptions import ValidationError
from psycopg2.errors import UniqueViolation, OperationalError

from backend_main.logging.loggers.app import setup_request_event_logging
from backend_main.util.json import error_json
from backend_main.validation.util import RequestValidationException


@web.middleware
async def error_middleware(request, handler):
    try:
        return await handler(request)

    except JSONDecodeError:
        request.log_event("WARNING", "request", "Failed to process JSON in request body.")
        raise web.HTTPBadRequest(text=error_json("Request body must be a valid JSON document."), content_type="application/json")

    except ValidationError as e:
        path = "JSON root" if len(e.absolute_path) == 0 else f"""'{"' > '".join(map(str, e.absolute_path))}'"""
        msg = f"JSON validation error at {path}: {e.message}"
        request.log_event("WARNING", "request", "Request body was not validated.", details=msg)
        raise web.HTTPBadRequest(text = error_json(msg), content_type="application/json")

    except RequestValidationException as e:
        request.log_event("WARNING", "request", "Invalid data in request body.", details=str(e))
        raise web.HTTPBadRequest(text=error_json(e), content_type="application/json")

    except UniqueViolation as e:
        msg = _get_uv_msg(e)
        request.log_event("WARNING", "request", "Invalid data in request body.", details=msg)
        raise web.HTTPBadRequest(text=error_json(msg), content_type="application/json")

    except OperationalError as e:
        request.log_event("ERROR", "request", "Failed to connect to the database.")
        _raise_500(request, e)

    except web.HTTPException as e:
        if type(e) == web.HTTPServiceUnavailable:
            request.log_event("WARNING", "request", "Request was not processed due to app shutdown.")

        raise

    except Exception as e:
        request.log_event("ERROR", "request", "Unexpected error during request processing.", exc_info=True)
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