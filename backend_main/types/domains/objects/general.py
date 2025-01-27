from pydantic import BaseModel, ConfigDict, Field, TypeAdapter
from typing import Literal, Annotated

from backend_main.types.common import PositiveInt, Name
from backend_main.types.domains.objects.attributes import ObjectType, UpsertedObjectAttributesAndTags
from backend_main.types.domains.objects.data import LinkIDTypeData, MarkdownIDTypeData, \
    ToDoListIDTypeData, CompositeIDTypeData


# Objects bulk upsert
class UpsertedLink(UpsertedObjectAttributesAndTags, LinkIDTypeData):
    """ Upserted link object attributes, tags & data. """
    model_config = ConfigDict(extra="forbid", strict=True)
    pass


class UpsertedMarkdown(UpsertedObjectAttributesAndTags, MarkdownIDTypeData):
    """ Upserted markdown object attributes, tags & data. """
    model_config = ConfigDict(extra="forbid", strict=True)
    pass


class UpsertedToDoList(UpsertedObjectAttributesAndTags, ToDoListIDTypeData):
    """ Upserted to-do list object attributes, tags & data. """
    model_config = ConfigDict(extra="forbid", strict=True)
    pass


class UpsertedComposite(UpsertedObjectAttributesAndTags, CompositeIDTypeData):
    """ Upserted to-do list object attributes, tags & data. """
    model_config = ConfigDict(extra="forbid", strict=True)
    pass


UpsertedObject = UpsertedLink | UpsertedMarkdown | UpsertedToDoList | UpsertedComposite
""" Object attributes, tags & data sent to /objects/bulk_upsert route. """

# # NOTE: dicriminated union of models is implemented using TypeAdapter,
# # as suggested here: https://github.com/pydantic/pydantic/discussions/4950.
# # Another implementation option is to use discriminated union sub-model a field
# #
# # NOTE: type union is enough when validating a list of items, adapter is required for validation of a single object
# _AnnotatedUpsertedObject = Annotated[UpsertedObject, Field(discriminator="object_type")]
# upsertedObjectAdapter: TypeAdapter[UpsertedObject] = TypeAdapter(_AnnotatedUpsertedObject)


# New to existing object IDs map
class ObjectsIDsMap(BaseModel):
    """
    Data class, containing a mapping between new object IDs from request data
    and IDs they receive when added to the database.
    """
    model_config = ConfigDict(extra="forbid", strict=True)
    
    map: dict[int, int]


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
