from backend_main.types.app import app_config_key
from backend_main.types.request import Request


def add_searchable_updates_for_tags(request: Request, tag_ids: list[int]) -> None:
    """ Adds provided `tag_ids` for `request["searchable_updates_tag_ids"]` or creates a new set with provided tag_ids. """
    if not request.config_dict[app_config_key].auxillary.enable_searchables_updates: return

    if "searchable_updates_tag_ids" not in request: request["searchable_updates_tag_ids"] = set()

    for tag_id in tag_ids:
        request["searchable_updates_tag_ids"].add(tag_id)


def add_searchable_updates_for_objects(request: Request, object_ids: list[int]) -> None:
    """ Adds provided `object_ids` for `request["searchable_updates_object_ids"]` or creates a new set with provided object_ids. """
    if not request.config_dict[app_config_key].auxillary.enable_searchables_updates: return

    if "searchable_updates_object_ids" not in request: request["searchable_updates_object_ids"] = set()

    for object_id in object_ids:
        request["searchable_updates_object_ids"].add(object_id)
