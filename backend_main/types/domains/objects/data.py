from collections import Counter
from pydantic import BaseModel, ConfigDict, Field, AnyUrl, field_serializer, model_validator, TypeAdapter
from typing import Literal, Annotated
from typing_extensions import Self

from backend_main.types.common import NonNegativeInt


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

    @model_validator(mode="after")
    def validate_to_do_list(self) -> Self:
        # Check if item numbers are unique
        c = Counter((i.item_number for i in self.items))
        non_unique_item_numbers = [n for n in c if c[n] > 1]
        if len(non_unique_item_numbers) > 0:
            raise ValueError(f"Received non-unique to-do list item numbers {non_unique_item_numbers}.")
        return self


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

    @model_validator(mode="after")
    def validate_composite(self) -> Self:
        self._ensure_unique_subobject_ids()
        self._ensure_unique_subobject_positions()
        self._normalize_subobject_positions()
        return self

    def _ensure_unique_subobject_ids(self) -> None:
        """ Check if subobjects IDs are unique."""
        c = Counter((so.subobject_id for so in self.subobjects))
        non_unique_subobject_ids = [i for i in c if c[i] > 1]
        if len(non_unique_subobject_ids) > 0:
            raise ValueError(f"Received non-unique subobject IDs {non_unique_subobject_ids}.")
    
    def _ensure_unique_subobject_positions(self) -> None:
        """ Check if row + column combinations are unique. """
        c = Counter(((so.column, so.row) for so in self.subobjects))
        non_unique_positions = [pos for pos in c if c[pos] > 1]
        if len(non_unique_positions) > 0:
            raise ValueError(f"Received non-unique subobject positions {non_unique_positions}.")
        
    def _normalize_subobject_positions(self) -> None:
        """ Normalizes subobject column & row positions to a sequential zero-based indexing. """
        # Build mapping between passed & normalized column & row positions
        columns: set[int] = set()
        column_rows: dict[int, set[int]] = {}
        for so in self.subobjects:
            columns.add(so.column)
            rows = column_rows.get(so.column, set())
            rows.add(so.row)
            column_rows[so.column] = rows
        
        columns_map = {c: i for i, c in enumerate(sorted(columns))}
        columns_rows_maps = {
            column: {r: i for i, r in enumerate(sorted(rows))}
            for column, rows in column_rows.items()
        }

        for so in self.subobjects:
            so.row = columns_rows_maps[so.column][so.row]    # use old column number as a map index
            so.column = columns_map[so.column]


class LinkIDTypeData(BaseModel):
    """
    Link object ID, type and data.
    """
    model_config = ConfigDict(extra="ignore", strict=True)

    object_id: int
    object_type: Literal["link"]
    object_data: Link


class MarkdownIDTypeData(BaseModel):
    """
    Markdown object ID, type and data.
    """
    model_config = ConfigDict(extra="ignore", strict=True)

    object_id: int
    object_type: Literal["markdown"]
    object_data: Markdown


class ToDoListIDTypeData(BaseModel):
    """
    To-do list object ID, type and data.
    """
    model_config = ConfigDict(extra="ignore", strict=True)

    object_id: int
    object_type: Literal["to_do_list"]
    object_data: ToDoList


class CompositeIDTypeData(BaseModel):
    """
    Composite object ID, type and data.
    """
    model_config = ConfigDict(extra="ignore", strict=True)

    object_id: int
    object_type: Literal["composite"]
    object_data: Composite


ObjectIDTypeData = LinkIDTypeData | MarkdownIDTypeData | ToDoListIDTypeData | CompositeIDTypeData
""" Object ID, type and data. """

# NOTE: dicriminated union of models is implemented using TypeAdapter,
# as suggested here: https://github.com/pydantic/pydantic/discussions/4950.
# Another implementation option is to use discriminated union sub-model a field
#
_AnnotatedObjectIDTypeData = Annotated[ObjectIDTypeData, Field(discriminator="object_type")]
objectIDTypeDataAdapter: TypeAdapter[ObjectIDTypeData] = TypeAdapter(_AnnotatedObjectIDTypeData)
