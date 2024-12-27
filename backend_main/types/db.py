from dataclasses import dataclass
from sqlalchemy import Column
from sqlalchemy.sql import FromClause
from sqlalchemy.sql.expression import ColumnOperators
from typing import Callable, Protocol, Any


# Common table stubs
class _TableCommon(Protocol):
    insert: Callable[[], Any]   # Insert, Update & Delete classes have some of their methods
    update: Callable[[], Any]   # generated in runtime, which is not recognised by MyPy
    delete: Callable[[], Any]
    join: "_TableJoin"


class _TableJoin(Protocol):
    def __call__(
        self,
        target: FromClause | _TableCommon,
        onclause: ColumnOperators | None = None,
        isouter: bool | None = False,
        full: bool | None = False
    ): ...


# settings
class _C_Settings(Protocol):
    setting_name: Column
    setting_value: Column
    is_public: Column


class _Settings(_TableCommon, Protocol):
    c: _C_Settings    


# users
class _C_Users(Protocol):
      user_id: Column
      registered_at: Column
      login: Column
      username: Column
      password: Column
      user_level: Column
      can_login: Column
      can_edit_objects: Column


class _Users(_TableCommon, Protocol):
     c: _C_Users


# sessions
class _C_Sessions(Protocol):
    user_id: Column
    access_token: Column
    expiration_time: Column


class _Sessions(_TableCommon, Protocol):
     c: _C_Sessions


# login_rate_limits
class _C_LoginRateLimits(Protocol):
    ip_address: Column
    failed_login_attempts: Column
    cant_login_until: Column


class _LoginRateLimits(_TableCommon, Protocol):
     c: _C_LoginRateLimits


# tags
class _C_Tags(Protocol):
    tag_id: Column
    created_at: Column
    modified_at: Column
    tag_name: Column
    tag_description: Column
    is_published: Column


class _Tags(_TableCommon, Protocol):
    c: _C_Tags


# objects
class _C_Objects(Protocol):
    object_id: Column
    object_type: Column
    created_at: Column
    modified_at: Column
    object_name: Column
    object_description: Column
    owner_id: Column
    is_published: Column
    display_in_feed: Column
    feed_timestamp: Column
    show_description: Column


class _Objects(_TableCommon, Protocol):
    c: _C_Objects


# objects_tags
class _C_ObjectsTags(Protocol):
     tag_id: Column
     object_id: Column


class _ObjectsTags(_TableCommon, Protocol):
    c: _C_ObjectsTags


# links
class _C_Links(Protocol):
    object_id: Column
    link: Column
    show_description_as_link: Column


class _Links(_TableCommon, Protocol):
    c: _C_Links


# markdown
class _C_Markdown(Protocol):
    object_id: Column
    raw_text: Column


class _Markdown(_TableCommon, Protocol):
    c: _C_Markdown


# to_do_lists
class _C_ToDoLists(Protocol):
    object_id: Column
    sort_type: Column


class _ToDoLists(_TableCommon, Protocol):
    c: _C_ToDoLists


# to_do_list_items
class _C_ToDoListItems(Protocol):
    object_id: Column
    item_number: Column
    item_state: Column
    item_text: Column
    commentary: Column
    indent: Column
    is_expanded: Column


class _ToDoListItems(_TableCommon, Protocol):
    c: _C_ToDoListItems


# composite_properties
class _C_CompositeProperties(Protocol):
    object_id: Column
    display_mode: Column
    numerate_chapters: Column


class _CompositeProperties(_TableCommon, Protocol):
    c: _C_CompositeProperties
    

# composite
class _C_Composite(Protocol):
    object_id: Column
    subobject_id: Column
    row: Column
    column: Column
    selected_tab: Column
    is_expanded: Column
    show_description_composite: Column
    show_description_as_link_composite: Column


class _Composite(_TableCommon, Protocol):
    c: _C_Composite


# searchables
class _C_Searchables(Protocol):
    object_id: Column
    tag_id: Column
    modified_at: Column
    text_a: Column
    text_b: Column
    text_c: Column
    searchable_tsv_russian: Column


class _Searchables(_TableCommon, Protocol):
    c: _C_Searchables


@dataclass
class AppTables:
    """
    Type provider for tables returend by `get_tables` function.
    Current type definitions provide a list of columns stored in `c` attribute of each table.

    NOTE: A better way to add typing would be to upgrade SQLAlchemy to v2 & use ORM for table definitions
    (which requires refactoring of existing queries). Additionally, some automatic mapping of SQLAlchemy
    to Pydantic models (such as SQLModel) could be useful.
    """
    settings: _Settings
    users: _Users
    sessions: _Sessions
    login_rate_limits: _LoginRateLimits
    tags: _Tags
    objects: _Objects
    objects_tags: _ObjectsTags
    links: _Links
    markdown: _Markdown
    to_do_lists: _ToDoLists
    to_do_list_items: _ToDoListItems
    composite_properties: _CompositeProperties
    composite: _Composite
    searchables: _Searchables
