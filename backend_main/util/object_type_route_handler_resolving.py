object_type_func_name_mapping = {"link": "links", "markdown": "markdown", "to_do_list": "to_do_lists", "composite": "composite"}


def get_object_type_route_handler(route, object_type):
    """ 
        Returns a handling function for provided `route` and `object_type`.
        `route` can be one of: "add", "update", "view".
        `object_type` is an exact value of objects.object_type DB column.
    """
    ot = object_type_func_name_mapping.get(object_type, object_type)
    return globals()[f"{route}_{ot}"]


# Imports are at the end of file to avoid circular import error
from backend_main.db_operations.objects_links import add_links, update_links
from backend_main.db_operations.objects_markdown import add_markdown, update_markdown
from backend_main.db_operations.objects_to_do_lists import add_to_do_lists, update_to_do_lists
from backend_main.db_operations.objects_composite import add_composite, update_composite
