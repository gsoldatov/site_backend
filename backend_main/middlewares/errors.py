"""
    Error handling middleware.
"""
from aiohttp import web
from json.decoder import JSONDecodeError
from jsonschema.exceptions import ValidationError as ValidationError_JSONSchema
from psycopg2.errors import UniqueViolation, OperationalError
from pydantic import ValidationError
from typing import NoReturn

from backend_main.util.json import error_json
from backend_main.validation.util import RequestValidationException

from backend_main.types.app import app_config_key
from backend_main.types.request import Request, Handler, request_log_event_key


@web.middleware
async def error_middleware(request: Request, handler: Handler) -> web.Response:
    try:
        return await handler(request)

    except JSONDecodeError:
        request[request_log_event_key]("WARNING", "request", "Failed to process JSON in request body.")
        raise web.HTTPBadRequest(text=error_json("Request body must be a valid JSON document."), content_type="application/json")
    
    except ValidationError as e:
        error_dict = e.json(include_url=False)
        request[request_log_event_key]("WARNING", "request", "Request body was not validated.", details=str(error_dict))
        raise web.HTTPBadRequest(text = error_json(error_dict), content_type="application/json")

    except ValidationError_JSONSchema as e:
        path = "JSON root" if len(e.absolute_path) == 0 else f"""'{"' > '".join(map(str, e.absolute_path))}'"""
        msg = f"JSON validation error at {path}: {e.message}"
        request[request_log_event_key]("WARNING", "request", "Request body was not validated.", details=msg)
        raise web.HTTPBadRequest(text = error_json(msg), content_type="application/json")

    except RequestValidationException as e:
        request[request_log_event_key]("WARNING", "request", "Invalid data in request body.", details=str(e))
        raise web.HTTPBadRequest(text=error_json(e), content_type="application/json")

    except UniqueViolation as e:
        msg = _get_unique_violation_error_message(e)
        request[request_log_event_key]("WARNING", "request", "Invalid data in request body.", details=msg)
        raise web.HTTPBadRequest(text=error_json(msg), content_type="application/json")

    except OperationalError as e:
        request[request_log_event_key]("ERROR", "request", "Failed to connect to the database.")
        _raise_500(request, e)

    except web.HTTPException as e:
        if type(e) == web.HTTPServiceUnavailable:
            request[request_log_event_key]("WARNING", "request", "Request was not processed due to app shutdown.")

        raise

    except Exception as e:
        request[request_log_event_key]("ERROR", "request", "Unexpected error during request processing.", exc_info=True)
        _raise_500(request, e)


def _raise_500(request: Request, exception: Exception) -> NoReturn:
    """
    Handles 500 error raising.
    If app is in debug mode, simply raises `exception` to allow aiohttp.server logger to capture error stacktrace.
    Otherwise raises web.HTTPInternalServerError with an overriden text.
    """
    if request.config_dict[app_config_key].app.debug:
        raise exception
    else:
        raise web.HTTPInternalServerError(text="Server failed to process request.")


def _get_unique_violation_error_message(e: Exception) -> str:
    """
    Generates an error message to return in HTTP response in case of a UniqueViolation error.
    """
    field_name_message_map = {
        "login": "Submitted login is unavailable.",
        "username": "Submitted username is unavailable.",
        "tag_name": "Submitted tag name already exists.",
    }
    error_text = str(e)

    for field_name in field_name_message_map:
        if error_text.find(field_name) > -1:
            return field_name_message_map[field_name]
    
    return f"Submitted data already exists."
