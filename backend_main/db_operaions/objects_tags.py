"""
    Common operations for updating objects_tags table.
"""
from datetime import datetime

from jsonschema import validate
from sqlalchemy import select, func
from sqlalchemy.sql import and_

from backend_main.schemas.objects_tags import objects_tags_update_schema
from backend_main.util.validation import ObjectsTagsUpdateException


async def update_objects_tags(request, conn, objects_tags_data, check_ids = False):
    """
    Performs remove and add operations for provided tag and object ids.
    
    If check_ids == True, IDs in object_ids list will be checked for existance in the database.
    IDs from added_tags are always checked.
    This functionality is not implemented for tag update case (when tag_ids is provided instead of object_ids).
    """
    validate(instance = objects_tags_data, schema = objects_tags_update_schema)
    # Update tags for objects
    if "object_ids" in objects_tags_data:
        if check_ids:
            await _check_object_ids(request, conn, objects_tags_data["object_ids"])
        tag_updates = {}
        tag_updates["removed_tag_ids"] = await _remove_tags_for_objects(request, conn, objects_tags_data)
        tag_updates["added_tag_ids"] = await _add_tags_for_objects(request, conn, objects_tags_data)
        return tag_updates
    # Update objects for tags
    else:
        object_updates = {}
        object_updates["removed_object_ids"] = await _remove_objects_for_tags(request, conn, objects_tags_data)
        object_updates["added_object_ids"] = await _add_objects_for_tags(request, conn, objects_tags_data)
        return object_updates

    
async def _add_tags_for_objects(request, conn, objects_tags_data):
    if len(objects_tags_data.get("added_tags", [])) == 0:
        return []
    
    ## Handle tag_ids passed in added_tags
    tags = request.app["tables"]["tags"]
    tag_ids = {id for id in objects_tags_data["added_tags"] if type(id) == int}
    
    if len(tag_ids) > 0:
        # Check if all of the provided tag_ids exist
        result = await conn.execute(select([tags.c.tag_id])
                                    .where(tags.c.tag_id.in_(tag_ids)))
        existing_tag_ids = {row["tag_id"] for row in await result.fetchall()}
        non_existing_tag_ids = tag_ids.difference(existing_tag_ids)
        if len(non_existing_tag_ids) > 0:
            raise ObjectsTagsUpdateException(f"Tag IDs {non_existing_tag_ids} do not exist.")
    
    ## Handle tag_names passed in "added_tags"
    tag_names = [name for name in objects_tags_data["added_tags"] if type(name) == str]
    lowered_tag_names = [name.lower() for name in tag_names]
    tag_ids_for_tag_names, lowered_existing_tag_names = set(), set()

    # Get existing tag_ids for provided string tag_names
    if len(tag_names) > 0:
        records = await conn.execute(select([tags.c.tag_id, func.lower(tags.c.tag_name).label("lowered_tag_name")])
                                    .where(func.lower(tags.c.tag_name).in_(lowered_tag_names))
        )
        for row in await records.fetchall():
            tag_ids_for_tag_names.add(row["tag_id"])
            lowered_existing_tag_names.add(row["lowered_tag_name"])
        
        # Get non-existing tag names and filter out possible duplicates in tag_names list
        new_tag_names = []
        for name in tag_names:
            if name not in lowered_existing_tag_names:
                new_tag_names.append(name)
                lowered_existing_tag_names.add(name.lower())
        tag_names = new_tag_names

    
    # Create new tags for non-existing tag_names
    if len(tag_names) > 0:
        current_time = datetime.utcnow()

        result = await conn.execute(tags.insert()
                                    .returning(tags.c.tag_id)
                                    .values([{
                                        "tag_name": name,
                                        "tag_description": None,
                                        "created_at": current_time,
                                        "modified_at": current_time
                                    } for name in tag_names ])
        )

        for row in await result.fetchall():
            tag_ids_for_tag_names.add(row["tag_id"])
    
    ## Update objects_tags table
    tag_ids.update(tag_ids_for_tag_names)

    # Delete existing combinations of provided object and tag IDs
    await _remove_tags_for_objects(request, conn, {"object_ids": objects_tags_data["object_ids"], "removed_tag_ids": tag_ids})

    # Add all combinations of object and tag IDs
    objects_tags = request.app["tables"]["objects_tags"]
    pairs = [{"object_id": object_id, "tag_id": tag_id} for object_id in objects_tags_data["object_ids"] for tag_id in tag_ids]

    await conn.execute(objects_tags.insert()
                       .values(pairs)
    )

    return list(tag_ids)
    

async def _remove_tags_for_objects(request, conn, objects_tags_data):
    # Delete data from objects_tags if:
    # 1. "object_ids" and "removed_tag_ids" in otd
    # 2. "object_ids" in otd and "remove_all_tags" == True
    objects_tags = request.app["tables"]["objects_tags"]

    # 1
    if "object_ids" in objects_tags_data and "removed_tag_ids" in objects_tags_data:
        result = await conn.execute(objects_tags.delete()
            .where(and_(
                    objects_tags.c.object_id.in_(objects_tags_data["object_ids"]), 
                    objects_tags.c.tag_id.in_(objects_tags_data["removed_tag_ids"])
            ))
            .returning(objects_tags.c.tag_id)
        )
        return list({row["tag_id"] for row in await result.fetchall()})
    
    # 2
    elif "object_ids" in objects_tags_data and objects_tags_data.get("remove_all_tags"):
        result = await conn.execute(objects_tags.delete()
            .where(objects_tags.c.object_id.in_(objects_tags_data["object_ids"]))
            .returning(objects_tags.c.tag_id)
        )
        return list({row["tag_id"] for row in await result.fetchall()})
    
    else:
       return []


async def _add_objects_for_tags(request, conn, objects_tags_data):
    added_object_ids = set(objects_tags_data.get("added_object_ids", []))
    if len(added_object_ids) == 0:
        return []
    
    # Check if all of the provided object ids exist
    await _check_object_ids(request, conn, added_object_ids)

    # Delete existing combinations of provided tag and object IDs
    await _remove_objects_for_tags(request, conn, {"tag_ids": objects_tags_data["tag_ids"], "removed_object_ids": added_object_ids})

    # Add all combinations of object and tag IDs
    objects_tags = request.app["tables"]["objects_tags"]
    pairs = [{"object_id": object_id, "tag_id": tag_id} for object_id in added_object_ids for tag_id in objects_tags_data["tag_ids"]]

    await conn.execute(objects_tags.insert()
                       .values(pairs)
    )

    return list(added_object_ids)


async def _remove_objects_for_tags(request, conn, objects_tags_data):
    # Delete data from objects_tags if:
    # 1. "tag_ids" and "removed_object_ids" in otd
    # 2. "tag_ids" in otd and "remove_all_objects" == True
    objects_tags = request.app["tables"]["objects_tags"]

    # 1
    if "tag_ids" in objects_tags_data and "removed_object_ids" in objects_tags_data:
        result = await conn.execute(objects_tags.delete()
            .where(and_(
                    objects_tags.c.object_id.in_(objects_tags_data["removed_object_ids"]), 
                    objects_tags.c.tag_id.in_(objects_tags_data["tag_ids"])
            ))
            .returning(objects_tags.c.object_id)
        )
        return list({row["object_id"] for row in await result.fetchall()})
    
    # 2
    elif "tag_ids" in objects_tags_data and objects_tags_data.get("remove_all_objects"):
        result = await conn.execute(objects_tags.delete()
            .where(objects_tags.c.tag_id.in_(objects_tags_data["tag_ids"]))
            .returning(objects_tags.c.object_id)
        )
        return list({row["object_id"] for row in await result.fetchall()})
    
    else:
       return []


async def _check_object_ids(request, conn, checked_object_ids):
    if type(checked_object_ids) != set:
        checked_object_ids = set(checked_object_ids)
    objects = request.app["tables"]["objects"]
    result = await conn.execute(select([objects.c.object_id])
                                .where(objects.c.object_id.in_(checked_object_ids)))
    existing_object_ids = {row["object_id"] for row in await result.fetchall()}
    non_existing_object_ids = checked_object_ids.difference(existing_object_ids)
    if len(non_existing_object_ids) > 0:
        raise ObjectsTagsUpdateException(f"Object IDs {non_existing_object_ids} do not exist.")
