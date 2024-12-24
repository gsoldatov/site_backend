"""
Auth-related SQLAlchemy constructs and filters.
"""
from sqlalchemy import select, true, Column
from sqlalchemy.sql import and_, or_, Select

from typing import Iterable
from backend_main.types.app import app_tables_key
from backend_main.types.request import Request, request_user_info_key


def get_objects_auth_filter_clause(
        request: Request,
        object_ids: Iterable[int] | None = None,
        object_ids_subquery: Select | None = None
    ):
    """
    Returns an SQLAlchemy 'where' clause, which:
    - filters non-published objects and objects with non-published tags if user is anonymous;
    - filters non-published objects of other users and objects with non-published tags if user has 'user' level;
    - 1 = 1 for 'admin' user level.

    `object_ids` or `object_ids_subquery` are used to specify object IDs, which are checked for being marked with non-published tags.
    """
    objects = request.config_dict[app_tables_key].objects
    ui = request[request_user_info_key]

    if ui.is_anonymous:
        return and_(
            objects.c.is_published == True,
            get_objects_with_published_tags_only_clause(request, object_ids, object_ids_subquery)
        )
    
    if ui.user_level == "admin":
        return true()
    
    # user
    return and_(
        or_(objects.c.owner_id == ui.user_id, objects.c.is_published == True),
        get_objects_with_published_tags_only_clause(request, object_ids, object_ids_subquery)
    )


def get_objects_data_auth_filter_clause(
        request: Request,
        object_id_column: Column,
        object_ids: Iterable[int]
    ):
    """
    Returns an SQL Alchemy 'where' clause with a subquery for applying objects' auth filters for `object_id_column`.
    """
    objects = request.config_dict[app_tables_key].objects
    ui = request[request_user_info_key]

    if ui.user_level == "admin":
        return object_id_column.in_(object_ids)
    
    objects_auth_filter_clause = get_objects_auth_filter_clause(request, object_ids=object_ids)

    return object_id_column.in_(
        select(objects.c.object_id)
        .where(and_(
            objects_auth_filter_clause,
            objects.c.object_id.in_(object_ids)
        ))
    )


def get_objects_with_published_tags_only_clause(
        request: Request,
        object_ids: Iterable[int] | None = None,
        object_ids_subquery: Select | None = None
    ):
    """
    Returns an SQL Alchemy 'where' clause subquery, which:
    - if user has admin level, does nothing;
    - if user has non-admin level, filters `objects.object_id` column with a subquery, 
      which filters out IDs with at least one non-published tag.
    
    To reduce the amount of objects' tags processing an iterable with object IDs `object_ids`
    or a subquery, which returns a list of object IDs `object_ids_subquery` must be provided.
    """
    objects = request.config_dict[app_tables_key].objects
    tags = request.config_dict[app_tables_key].tags
    objects_tags = request.config_dict[app_tables_key].objects_tags
    ui = request[request_user_info_key]

    if ui.user_level == "admin": return true()

    object_ids_filter: Iterable[int] | Select
    if object_ids is not None:
        object_ids_filter = object_ids 
    elif object_ids_subquery is not None:
        object_ids_filter = object_ids_subquery
    else:
        raise RuntimeError("Either `object_ids` or `object_ids_subquery` must be provided.")

    return objects.c.object_id.notin_(
        select(objects_tags.c.object_id)
        .distinct()
        .select_from(objects_tags.join(tags, objects_tags.c.tag_id == tags.c.tag_id))
        .where(and_(
            objects_tags.c.object_id.in_(object_ids_filter),    # type: ignore[arg-type]
                                                                # `Select` class is not present in SA stubs
            get_tags_auth_filter_clause(request, is_published=False)
        ))
    )


def get_tags_auth_filter_clause(
        request: Request,
        is_published: bool = True
    ):
    """
    Returns an SQL Alchemy 'where' clause for filtering tags on `is_published` field with the provided `is_published` value:
    - 1 = 1 for admin user level;
    - tags.is_published = `is_published` if user has 'user' level;
    - tags.is_published = `is_published` if user is anonymous.
    """
    tags = request.config_dict[app_tables_key].tags
    ui = request[request_user_info_key]

    if ui.user_level == "admin": return true()

    return tags.c.is_published == is_published
