"""
    Common operations with objects_tags table.
"""
from datetime import datetime

from aiohttp import web
from jsonschema import validate
from sqlalchemy import select, func
from sqlalchemy.sql import and_

from backend_main.db_operations.auth import check_if_user_owns_objects, \
    check_if_user_owns_all_tagged_objects, get_objects_auth_filter_clause

from backend_main.util.validation import RequestValidationException


async def view_objects_tags(request, object_ids = None, tag_ids = None):
    """
        Returns a collection of RowProxy objects with tag and object IDs for the objects (tags) with provided object_ids (tag_ids).
    """
    if object_ids is None and tag_ids is None:
        raise TypeError("view_objects_tags requires object or tag IDs.")
    if object_ids is not None and tag_ids is not None:
        raise TypeError("view_objects_tags can't receive object and tag IDs at the same time.")

    objects = request.config_dict["tables"]["objects"]
    objects_tags = request.config_dict["tables"]["objects_tags"]

    # Objects filter for non 'admin` user level
    auth_filter_clause = get_objects_auth_filter_clause(request)

    result = await request["conn"].execute(
        select([objects_tags.c.object_id, objects_tags.c.tag_id])
        .select_from(objects_tags.join(objects, objects_tags.c.object_id == objects.c.object_id))   # join objects table to apply auth filters
        .where(auth_filter_clause)
        .where(objects_tags.c.object_id.in_(object_ids) if object_ids is not None else 1 == 1)
        .where(objects_tags.c.tag_id.in_(tag_ids) if tag_ids is not None else 1 == 1)
    )

    # result = await request["conn"].execute(
    #     select([objects_tags.c.object_id, objects_tags.c.tag_id])
    #     .where(objects_tags.c.object_id.in_(object_ids) if object_ids is not None else 1 == 1)
    #     .where(objects_tags.c.tag_id.in_(tag_ids) if tag_ids is not None else 1 == 1)
    # )

    return await result.fetchall()


async def update_objects_tags(request, objects_tags_data, check_ids = False):
    """
    Performs remove and add operations for provided tag and object ids.
    
    If check_ids == True, IDs in object_ids list will be checked for existance in the database.
    IDs from added_tags are always checked.
    This functionality is not implemented for tag update case (when tag_ids is provided instead of object_ids).

    NOTE: tag update case is also not properly tested for correctness of auth checks & updates made.
    """
    # Update tags for objects
    if "object_ids" in objects_tags_data:
        # Check if user can update objects
        await check_if_user_owns_objects(request, objects_tags_data["object_ids"])

        # Check if objects exist
        if check_ids:
            await _check_object_ids(request, objects_tags_data["object_ids"])
        tag_updates = {}

        tag_updates["removed_tag_ids"] = await _remove_tags_for_objects(request, objects_tags_data)
        tag_updates["added_tag_ids"] = await _add_tags_for_objects(request, objects_tags_data)
        return tag_updates
    # Update objects for tags
    else:
        # Check if user can update objects
        await auth_check_for_tags_update(request, objects_tags_data)

        object_updates = {}
        object_updates["removed_object_ids"] = await _remove_objects_for_tags(request, objects_tags_data)
        object_updates["added_object_ids"] = await _add_objects_for_tags(request, objects_tags_data)
        return object_updates

    
async def _add_tags_for_objects(request, objects_tags_data):
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
            raise RequestValidationException(f"Tag IDs {non_existing_tag_ids} do not exist.")
    
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

    
    # Create new tags for non-existing tag_names
    if len(tag_names) > 0:
        # Raise 403 if not an admin and trying to add new tags
        if request.user_info.user_level != "admin":
            raise web.HTTPForbidden(text=error_json("Users are not allowed to add new tags."), content_type="application/json")

        current_time = datetime.utcnow()

        result = await request["conn"].execute(
            tags.insert()
            .returning(tags.c.tag_id)
            .values([{
                "tag_name": name,
                "tag_description": "",
                "created_at": current_time,
                "modified_at": current_time
            } for name in tag_names ])
        )

        for row in await result.fetchall():
            tag_ids_for_tag_names.add(row["tag_id"])
    
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

    return list(tag_ids)
    

async def _remove_tags_for_objects(request, objects_tags_data):
    # Delete data from objects_tags if:
    # 1. "object_ids" and "removed_tag_ids" in otd
    # 2. "object_ids" in otd and "remove_all_tags" == True
    objects_tags = request.config_dict["tables"]["objects_tags"]

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
        raise RequestValidationException(f"Object IDs {non_existing_object_ids} do not exist.")


async def auth_check_for_tags_update(request, objects_tags_data):
    """
    Checks if user owns the updated objects. 
    If `remove_all_objects` flag is passed in `objects_tags_data`, checks all objects to be untagged.
    """
    if "remove_all_objects" in objects_tags_data:
        await check_if_user_owns_all_tagged_objects(request, objects_tags_tags["tag_ids"])
    else:
        object_ids = [o for o in objects_tags_data["added_object_ids"]] if "added_object_ids" in objects_tags_data else []
        object_ids.extend(objects_tags_data.get("removed_object_ids", []))
        await check_if_user_owns_objects(request, object_ids)