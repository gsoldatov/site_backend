from pydantic import BaseModel, ConfigDict, Field, AnyUrl, field_serializer, TypeAdapter
from typing import Literal, Annotated

from backend_main.types.common import PositiveInt, NonNegativeInt, Name, Datetime


ObjectType = Literal["link", "markdown", "to_do_list", "composite"]


class ObjectAttributesAndTags(BaseModel):
    """
    Object attributes and current tag IDs, as returned by /objects/view route.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    object_id: int
    object_type: ObjectType
    created_at: Datetime
    modified_at: Datetime
    object_name: Name
    object_description: str
    owner_id: PositiveInt
    is_published: bool
    display_in_feed: bool
    feed_timestamp: Datetime | None
    show_description: bool
    current_tag_ids: list[PositiveInt]


class Link(BaseModel):
    """
    Link object data.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    link: AnyUrl
    show_description_as_link: bool

    @field_serializer("link")
    def serialize_url(self, link: AnyUrl) -> str:
        return str(link)


class Markdown(BaseModel):
    """
    Markdown object data.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    raw_text: str = Field(min_length=1)


class ToDoListItem(BaseModel):
    """
    A single to-do list item.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    item_number: NonNegativeInt
    item_state: Literal["active", "completed", "optional", "cancelled"]
    item_text: str 
    commentary: str 
    indent: NonNegativeInt
    is_expanded: bool


class ToDoList(BaseModel):
    """
    To-do list object data.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    items: list[ToDoListItem] = Field(min_length=1)
    sort_type: Literal["default", "state"]


class CompositeSubobject(BaseModel):
    """
    A single composite subobject data.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    subobject_id: int
    row: NonNegativeInt
    column: NonNegativeInt
    selected_tab: NonNegativeInt
    is_expanded: bool
    show_description_composite: Literal["yes", "no", "inherit"]
    show_description_as_link_composite: Literal["yes", "no", "inherit"]


class Composite(BaseModel):
    """
    Composite object data.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    subobjects: list[CompositeSubobject]
    display_mode: Literal["basic", "multicolumn", "grouped_links", "chapters"]
    numerate_chapters: bool


class LinkIDTypeData(BaseModel):
    """
    Link object ID, type and data.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    object_id: int
    object_type: Literal["link"]
    object_data: Link


class MarkdownIDTypeData(BaseModel):
    """
    Markdown object ID, type and data.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    object_id: int
    object_type: Literal["markdown"]
    object_data: Markdown


class ToDoListIDTypeData(BaseModel):
    """
    To-do list object ID, type and data.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    object_id: int
    object_type: Literal["to_do_list"]
    object_data: ToDoList


class CompositeIDTypeData(BaseModel):
    """
    Composite object ID, type and data.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    object_id: int
    object_type: Literal["composite"]
    object_data: Composite


# NOTE: dicriminated union of models is implemented using TypeAdapter,
# as suggested here: https://github.com/pydantic/pydantic/discussions/4950.
# Another implementation option is to use discriminated union sub-model a field
ObjectIDTypeData = LinkIDTypeData | MarkdownIDTypeData | ToDoListIDTypeData | CompositeIDTypeData
""" Object ID, type and data. """
_AnnotatedObjectIDTypeData = Annotated[ObjectIDTypeData, Field(discriminator="object_type")]
objectIDTypeDataAdapter: TypeAdapter[ObjectIDTypeData] = TypeAdapter(_AnnotatedObjectIDTypeData)


# class ObjectAttributesAndTagsMap(BaseModel):
#     """
#     Mapping between object IDs and corresponding attributes & tags.
#     """
#     model_config = ConfigDict(extra="forbid", strict=True)

#     map: dict[int, ObjectAttributesAndTags]


# Objects pagination
class ObjectsPaginationInfo(BaseModel):
    """
    Objects pagination info attributes, used in request.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    page: int = Field(ge=1)
    items_per_page: int = Field(ge=1)
    order_by: Literal["object_name", "modified_at", "feed_timestamp"]
    sort_order: Literal["asc", "desc"]
    filter_text: str = Field(default="", max_length=255)
    object_types: list[ObjectType] = Field(default_factory=list, max_length=4)
    tags_filter: list[PositiveInt] = Field(default_factory=list, max_length=100)
    show_only_displayed_in_feed: bool = Field(default=False)


class ObjectsPaginationInfoWithResult(ObjectsPaginationInfo):
    """
    Objects pagination info attributes and query results.
    """
    object_ids: list[int]
    total_items: int


# Objects search
class ObjectsSearchQuery(BaseModel):
    """
    Objects search query attributes.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    query_text: Name
    maximum_values: int = Field(ge=1, le=100)
    existing_ids: list[PositiveInt] = Field(max_length=100)


# Composite hierarchy
class CompositeHierarchy(BaseModel):
    """
    Object IDs present in the hierarchy of a composite object.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    composite: list[int]
    non_composite: list[int]
