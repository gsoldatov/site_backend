from jsonschema import validate
from backend_main.validation.schemas.object_data import link_object_data, markdown_object_data, \
    to_do_list_object_data, composite_object_data


class RequestValidationException(Exception):
    pass


def validate_object_data(object_type, object_data):
    """ Calls a specific schema validator for `object_data` based on its `object_type`."""
    if object_type == "link":
        validate(object_data, link_object_data)
    elif object_type == "markdown":
        validate(object_data, markdown_object_data)
    elif object_type == "to_do_list":
        validate(object_data, to_do_list_object_data)
    elif object_type == "composite":
        validate(object_data, composite_object_data)
    else:
        raise NotImplementedError(f"Could not resolve object data schema for object type '{object_type}'.")
