"""
    Common operations with objects_tags table.
"""
from aiohttp import web
from sqlalchemy import select, func, true
from sqlalchemy.sql import and_

from backend_main.db_operations.auth import check_if_user_owns_objects, \
    check_if_user_owns_all_tagged_objects, get_objects_auth_filter_clause, get_tags_auth_filter_clause
from backend_main.middlewares.connection import start_transaction

from backend_main.util.json import error_json
from backend_main.util.searchables import add_searchable_updates_for_tags
from backend_main.validation.util import RequestValidationException


async def view_objects_tags(request, object_ids = None, tag_ids = None):
    """
        Returns a collection of RowProxy objects with tag and object IDs for the objects (tags) with provided object_ids (tag_ids).
    """
    if object_ids is None and tag_ids is None:
        raise TypeError("view_objects_tags requires object or tag IDs.")
    if object_ids is not None and tag_ids is not None:
        raise TypeError("view_objects_tags can't receive object and tag IDs at the same time.")

    objects = request.config_dict["tables"]["objects"]
    tags = request.config_dict["tables"]["tags"]
    objects_tags = request.config_dict["tables"]["objects_tags"]

    # Query tags for `object_ids`
    if object_ids:
        # Objects filter for non 'admin` user level
        objects_auth_filter_clause = get_objects_auth_filter_clause(request, object_ids=object_ids)

        result = await request["conn"].execute(
        select([objects_tags.c.object_id, objects_tags.c.tag_id])
        .select_from(objects_tags.join(objects, objects_tags.c.object_id == objects.c.object_id))   # join objects table to apply objects auth filter
        .where(and_(
            objects_tags.c.object_id.in_(object_ids),   # select rows for provided `object_ids`
            objects_auth_filter_clause                  # filter with objects auth clause
        )))

        return await result.fetchall()
    
    # Query objects for `tag_ids`
    else:
        tags_auth_filter_clause = get_tags_auth_filter_clause(request, is_published=True)
        objects_auth_filter_clause = get_objects_auth_filter_clause(request, object_ids_subquery=(
            select([objects_tags.c.object_id])
            .distinct()
            .where(objects_tags.c.tag_id.in_(tag_ids))
        ))

        # Get pairs wihtout filtering objects with non-published tags
        result = await request["conn"].execute(
        select([objects_tags.c.object_id, objects_tags.c.tag_id])
        .select_from(
                objects_tags
                .join(tags, objects_tags.c.tag_id == tags.c.tag_id))   # join tags table to apply tags auth filter
                .join(objects, objects_tags.c.object_id == objects.c.object_id)
        .where(and_(
            objects_tags.c.tag_id.in_(tag_ids),         # select rows for provided `tag_ids`
            tags_auth_filter_clause,                    # filter with tags auth clause
            objects_auth_filter_clause                  # filter with objects auth clause
        )))

        return await result.fetchall()


async def update_objects_tags(request, objects_tags_data, check_ids = False):
    """
    Performs remove and add operations for provided tag and object ids.
    
    If check_ids == True, IDs in object_ids list will be checked for existance in the database.
    IDs from added_tags are always checked.
    This functionality is not implemented for tag update case (when tag_ids is provided instead of object_ids).

    NOTE: if objects for tags update case becomes used, auth checks must be added and properly tested
    (anonymous restriction, object owning, non-published tag usage by non-admins).
    """
    # Ensure a transaction is started
    await start_transaction(request)

    # Update tags for objects
    if "object_ids" in objects_tags_data:
        # Check if user can update objects
        await check_if_user_owns_objects(request, objects_tags_data["object_ids"])

        # Check if objects exist
        if check_ids:
            await _check_object_ids(request, objects_tags_data["object_ids"])
        tag_updates = {}

        tag_updates["removed_tag_ids"] = await _remove_tags_for_objects(request, objects_tags_data)
        if len(tag_updates["removed_tag_ids"]) > 0: # Log here instead of _remove_tags_for_objects to avoid logging updates as deletions
            request.log_event("INFO", "db_operation", "Removed objects' tags.", details=f"object_ids = {objects_tags_data['object_ids']}, tag_ids = {tag_updates['removed_tag_ids']}")
        tag_updates["added_tag_ids"] = await _add_tags_for_objects(request, objects_tags_data)
        return tag_updates
    # Update objects for tags
    else:
        # Check if user can update objects
        await auth_check_for_tags_update(request, objects_tags_data)

        object_updates = {}
        object_updates["removed_object_ids"] = await _remove_objects_for_tags(request, objects_tags_data)
        if len(object_updates["removed_object_ids"]) > 0: # Log here instead of _remove_tags_for_objects to avoid logging updates as deletions
            request.log_event("INFO", "db_operation", "Removed tags' objects.", details=f"tag_ids = {objects_tags_data['tag_ids']}, object_ids = {object_updates['removed_object_ids']}")
        object_updates["added_object_ids"] = await _add_objects_for_tags(request, objects_tags_data)
        return object_updates

    
async def _add_tags_for_objects(request, objects_tags_data):
    """
    NOTE: check if a transaction is needed if this function is used outside of `update_objects_tags`
    """

    if len(objects_tags_data.get("added_tags", [])) == 0:
        return []
    
    ## Handle tag_ids passed in added_tags
    tags = request.config_dict["tables"]["tags"]
    tag_ids = {id for id in objects_tags_data["added_tags"] if type(id) == int}
    
    if len(tag_ids) > 0:
        # Check if all of the provided tag_ids exist
        result = await request["conn"].execute(
            select([tags.c.tag_id])
            .where(tags.c.tag_id.in_(tag_ids))
        )
        existing_tag_ids = {row["tag_id"] for row in await result.fetchall()}
        non_existing_tag_ids = tag_ids.difference(existing_tag_ids)
        if len(non_existing_tag_ids) > 0:
            msg = "Attempted to add non-existing tag(-s) to objects."
            request.log_event("WARNING", "db_operation", msg, details=f"tag_ids = {non_existing_tag_ids}")
            raise RequestValidationException(msg)
    
    ## Handle tag_names passed in "added_tags"
    tag_names = [name for name in objects_tags_data["added_tags"] if type(name) == str]
    lowered_tag_names = [name.lower() for name in tag_names]
    tag_ids_for_tag_names, lowered_existing_tag_names = set(), set()

    # Get existing tag_ids for provided string tag_names
    if len(tag_names) > 0:
        records = await request["conn"].execute(
            select([tags.c.tag_id, func.lower(tags.c.tag_name).label("lowered_tag_name")])
            .where(func.lower(tags.c.tag_name).in_(lowered_tag_names))
        )
        for row in await records.fetchall():
            tag_ids_for_tag_names.add(row["tag_id"])
            lowered_existing_tag_names.add(row["lowered_tag_name"])
        
        # Get non-existing tag names and filter out possible duplicates in tag_names list
        new_tag_names = []
        for name in tag_names:
            if name.lower() not in lowered_existing_tag_names:
                new_tag_names.append(name)
                lowered_existing_tag_names.add(name.lower())
        tag_names = new_tag_names
    
    # Check if non-admins add published existing tags only
    if request.user_info.user_level != "admin":
        result = await request["conn"].execute(
            select([func.count()])
            .where(get_tags_auth_filter_clause(request, is_published=False))
        )
        if (await result.fetchone())[0] > 0:
            request.log_event("WARNING", "db_operation", "Attempted to add non-published tags as a non-admin.")
            raise web.HTTPForbidden(text=error_json("Cannot add specified tags."), content_type="application/json")
    
    # Create new tags for non-existing tag_names
    if len(tag_names) > 0:
        # Raise 403 if not an admin and trying to add new tags
        if request.user_info.user_level != "admin":
            msg = "Attempted to add new tags as a non-admin."
            request.log_event("WARNING", "db_operation", msg)
            raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")

        request_time = request["time"]
        new_tag_ids = []

        result = await request["conn"].execute(
            tags.insert()
            .returning(tags.c.tag_id)
            .values([{
                "created_at": request_time,
                "modified_at": request_time,
                "tag_name": name,
                "tag_description": "",
                "is_published": True
            } for name in tag_names])
        )

        for row in await result.fetchall():
            new_tag_ids.append(row["tag_id"])
            tag_ids_for_tag_names.add(row["tag_id"])
        
        # Add new tags as pending for `searchables` update
        request.log_event("INFO", "db_operation", "Added new tags during objects' tag update.", details=f"tag_ids = {new_tag_ids}")
        add_searchable_updates_for_tags(request, new_tag_ids)
    
    ## Update objects_tags table
    tag_ids.update(tag_ids_for_tag_names)

    # Delete existing combinations of provided object and tag IDs
    await _remove_tags_for_objects(request, {"object_ids": objects_tags_data["object_ids"], "removed_tag_ids": tag_ids})

    # Add all combinations of object and tag IDs
    objects_tags = request.config_dict["tables"]["objects_tags"]
    pairs = [{"object_id": object_id, "tag_id": tag_id} for object_id in objects_tags_data["object_ids"] for tag_id in tag_ids]

    await request["conn"].execute(
        objects_tags.insert()
        .values(pairs)
    )

    request.log_event("INFO", "db_operation", "Updated objects' tags.", details=f"object_ids = {objects_tags_data['object_ids']} tag_ids = {tag_ids}")
    return list(tag_ids)
    

async def _remove_tags_for_objects(request, objects_tags_data):
    # Delete data from objects_tags if:
    # 1. "object_ids" and "removed_tag_ids" in otd
    # 2. "object_ids" in otd and "remove_all_tags" == True
    objects_tags = request.config_dict["tables"]["objects_tags"]
    tags = request.config_dict["tables"]["tags"]
    
    # Check if non-admins delete published tags only
    if request.user_info.user_level != "admin":
        removed_tags_clause = true() if objects_tags_data.get("remove_all_tags") else objects_tags.c.tag_id.in_(objects_tags_data["removed_tag_ids"])
        result = await request["conn"].execute(
            select([func.count()])
            .select_from(objects_tags.join(tags, objects_tags.c.tag_id == tags.c.tag_id))
            .where(and_(
                get_tags_auth_filter_clause(request, is_published=False),
                removed_tags_clause,
                objects_tags.c.object_id.in_(objects_tags_data["object_ids"])
            ))
        )

        if (await result.fetchone())[0] > 0:
            request.log_event("WARNING", "db_operation", "Attempted to delete non-published tags as a non-admin.")
            raise web.HTTPForbidden(text=error_json("Cannot delete tags."), content_type="application/json")

    # 1
    if "object_ids" in objects_tags_data and "removed_tag_ids" in objects_tags_data:
        result = await request["conn"].execute(
            objects_tags.delete()
            .where(and_(
                    objects_tags.c.object_id.in_(objects_tags_data["object_ids"]), 
                    objects_tags.c.tag_id.in_(objects_tags_data["removed_tag_ids"])
            ))
            .returning(objects_tags.c.tag_id)
        )
        return list({row["tag_id"] for row in await result.fetchall()})
    
    # 2
    elif "object_ids" in objects_tags_data and objects_tags_data.get("remove_all_tags"):
        result = await request["conn"].execute(
            objects_tags.delete()
            .where(objects_tags.c.object_id.in_(objects_tags_data["object_ids"]))
            .returning(objects_tags.c.tag_id)
        )
        return list({row["tag_id"] for row in await result.fetchall()})
    
    else:
       return []


async def _add_objects_for_tags(request, objects_tags_data):
    """
    NOTE: check if a transaction is needed if this function is used outside of `update_objects_tags`
    """
    
    added_object_ids = set(objects_tags_data.get("added_object_ids", []))
    if len(added_object_ids) == 0:
        return []
    
    # Check if all of the provided object ids exist
    await _check_object_ids(request, added_object_ids)

    # Delete existing combinations of provided tag and object IDs
    await _remove_objects_for_tags(request, {"tag_ids": objects_tags_data["tag_ids"], "removed_object_ids": added_object_ids})

    # Add all combinations of object and tag IDs
    objects_tags = request.config_dict["tables"]["objects_tags"]
    pairs = [{"object_id": object_id, "tag_id": tag_id} for object_id in added_object_ids for tag_id in objects_tags_data["tag_ids"]]

    await request["conn"].execute(
        objects_tags.insert()
        .values(pairs)
    )

    request.log_event("INFO", "db_operation", "Updated tags' objects.", details=f"tag_ids = {objects_tags_data['tag_ids']} object_ids = {added_object_ids}")
    return list(added_object_ids)


async def _remove_objects_for_tags(request, objects_tags_data):
    # Delete data from objects_tags if:
    # 1. "tag_ids" and "removed_object_ids" in otd
    # 2. "tag_ids" in otd and "remove_all_objects" == True
    objects_tags = request.config_dict["tables"]["objects_tags"]

    # 1
    if "tag_ids" in objects_tags_data and "removed_object_ids" in objects_tags_data:
        result = await request["conn"].execute(
            objects_tags.delete()
            .where(and_(
                    objects_tags.c.object_id.in_(objects_tags_data["removed_object_ids"]), 
                    objects_tags.c.tag_id.in_(objects_tags_data["tag_ids"])
            ))
            .returning(objects_tags.c.object_id)
        )
        return list({row["object_id"] for row in await result.fetchall()})
    
    # 2
    elif "tag_ids" in objects_tags_data and objects_tags_data.get("remove_all_objects"):
        result = await request["conn"].execute(
            objects_tags.delete()
            .where(objects_tags.c.tag_id.in_(objects_tags_data["tag_ids"]))
            .returning(objects_tags.c.object_id)
        )
        return list({row["object_id"] for row in await result.fetchall()})
    
    else:
       return []


async def _check_object_ids(request, checked_object_ids):
    if type(checked_object_ids) != set:
        checked_object_ids = set(checked_object_ids)
    objects = request.config_dict["tables"]["objects"]
    result = await request["conn"].execute(
        select([objects.c.object_id])
        .where(objects.c.object_id.in_(checked_object_ids))
    )
    existing_object_ids = {row["object_id"] for row in await result.fetchall()}
    non_existing_object_ids = checked_object_ids.difference(existing_object_ids)
    if len(non_existing_object_ids) > 0:
        msg = "Objects do not exist."
        request.log_event("WARNING", "db_operation", msg, details=f"object_ids = {non_existing_object_ids}")
        raise RequestValidationException(msg)


async def auth_check_for_tags_update(request, objects_tags_data):
    """
    Checks if user owns the updated objects. 
    If `remove_all_objects` flag is passed in `objects_tags_data`, checks all objects to be untagged.
    """
    if "remove_all_objects" in objects_tags_data:
        await check_if_user_owns_all_tagged_objects(request, objects_tags_data["tag_ids"])
    else:
        object_ids = [o for o in objects_tags_data["added_object_ids"]] if "added_object_ids" in objects_tags_data else []
        object_ids.extend(objects_tags_data.get("removed_object_ids", []))
        await check_if_user_owns_objects(request, object_ids)
