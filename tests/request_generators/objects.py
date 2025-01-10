def get_objects_delete_body(object_ids: list[int] | None = None, delete_subobjects: bool = False):
    """ Returns request body for /objects/delete route. """
    return { 
        "object_ids": object_ids if object_ids is not None else [1],
        "delete_subobjects": delete_subobjects
    }
