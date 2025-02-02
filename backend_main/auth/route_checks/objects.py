"""
/objects/... route auth checks, which rely on request data.
"""
from aiohttp import web
from sqlalchemy import select

from backend_main.auth.route_access.common import forbid_anonymous
from backend_main.util.json import error_json

from backend_main.types.app import app_tables_key
from backend_main.types.request import Request, request_log_event_key, request_user_info_key, request_connection_key, \
    request_auth_caches_key
from backend_main.types.domains.objects.attributes import UpsertedObjectAttributes


async def authorize_objects_modification(request: Request, object_ids: list[int]):
    """
    Checks if `request[request_user_info_key].user_id` is an admin or a user owning all objects with the provided `object_ids`.
    Raises 401 for anonymous.
    Raises 403 if user is not admin and does not own at least one object. Non-existing objects do not trigger the exception.
    """
    forbid_anonymous(request)

    if request[request_user_info_key].user_level != "admin":
        # Check cache & handle empty `object_ids`
        unchecked_object_ids = set(object_ids).difference(request[request_auth_caches_key].modifiable_object_ids)
        if len(unchecked_object_ids) == 0: return

        # Run auth check query
        objects = request.config_dict[app_tables_key].objects
        user_id = request[request_user_info_key].user_id

        result = await request[request_connection_key].execute(
            select(objects.c.object_id, objects.c.owner_id)
            .where(objects.c.object_id.in_(unchecked_object_ids))
        )

        not_owned_objects = [o[0] for o in await result.fetchall() if o[1] != user_id]

        # Handle errors & update cache
        if len(not_owned_objects) > 0:
            msg = "User does not own object(-s)."
            request[request_log_event_key]("WARNING", "auth", msg, details={"user_id": user_id, "object_ids": not_owned_objects})
            raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")
        
        request[request_auth_caches_key].modifiable_object_ids.update(unchecked_object_ids)


def authorize_object_owner_modification(
        request: Request,
        upserted_objects_attributes: list[UpsertedObjectAttributes]
    ) -> None:
    """
    Checks `owner_id` values from `upserted_objects_attributes` can be set by `request` issuer.
    Raises 401 for anonymous.
    Raises 403 for non-admins, who try to set any other user ID as object owners.
    """
    forbid_anonymous(request)

    if request[request_user_info_key].user_level != "admin":
        user_id = request[request_user_info_key].user_id
        unallowed_owner_ids = list(set((o.owner_id for o in upserted_objects_attributes if o.owner_id != user_id)))
        if len(unallowed_owner_ids) > 0:
            msg = "Object owner update is not allowed."
            request[request_log_event_key]("WARNING", "auth", msg, details={"user_id": user_id, "unallowed_owners": unallowed_owner_ids})
            raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")


# async def authorize_tagged_objects_modification(request: Request, tag_ids: list[int]):
#     """
#     Checks is `request[request_user_info_key].user_id` is an admin or a user owning all objects tagged with the provided `tag_ids`.
#     Raises 401 for anonymous.
#     Raises 403 if user is not admin and does not own at least one object.
#     """
#     if len(tag_ids) == 0: return

#     forbid_anonymous(request)

#     if request[request_user_info_key].user_level != "admin":
#         objects = request.config_dict[app_tables_key].objects
#         objects_tags = request.config_dict[app_tables_key].objects_tags
#         user_id = request[request_user_info_key].user_id

#         result = await request[request_connection_key].execute(
#             select(objects.c.object_id, objects.c.owner_id)
#             .where(objects.c.object_id.in_(
#                 select(objects_tags.c.object_id)
#                 .distinct()
#                 .where(objects_tags.c.tag_id.in_(tag_ids))
#             ))
#         )

#         not_owned_objects = [o[0] for o in await result.fetchall() if o[1] != user_id]

#         if len(not_owned_objects) > 0:
#             msg = "User does not own object(-s)."
#             request[request_log_event_key]("WARNING", "auth", msg, details={"user_id": user_id, "object_ids": not_owned_objects})
#             raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")
