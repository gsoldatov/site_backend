from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Literal, overload, Any

from backend_main.types.common import PositiveInt


class SearchableItem:
    """
    Data class for accumulating searchable text of an item.
    Stores item ID and searchable texts of A, B & C search weight levels.
    """
    def __init__(self, item_id: PositiveInt | None = None, text_a = "", text_b = "", text_c = ""):
        self.item_id = item_id
        self.text_a = text_a
        self.text_b = text_b
        self.text_c = text_c
    
    @overload
    def __add__(self, x: dict) -> "SearchableItem": ...

    @overload
    def __add__(self, x: "SearchableItem") -> "SearchableItem": ...
    
    def __add__(self, x: Any) -> "SearchableItem":   # type union can't be done with a type & a string
        if type(x) == dict:
            new_text_a = self.text_a + (" " if len(self.text_a) > 0 else "") + x.get("text_a", "")
            new_text_b = self.text_b + (" " if len(self.text_b) > 0 else "") + x.get("text_b", "")
            new_text_c = self.text_c + (" " if len(self.text_c) > 0 else "") + x.get("text_c", "")
            return SearchableItem(self.item_id, new_text_a, new_text_b, new_text_c)
        
        if type(x) == SearchableItem:
            new_text_a = self.text_a + (" " if len(self.text_a) > 0 else "") + x.text_a
            new_text_b = self.text_b + (" " if len(self.text_b) > 0 else "") + x.text_b
            new_text_c = self.text_c + (" " if len(self.text_c) > 0 else "") + x.text_c
            return SearchableItem(self.item_id, new_text_a, new_text_b, new_text_c)
        
        return NotImplemented
    
    def __str__(self) -> str:
        return f"<SearchableItem id = {self.item_id}>" + \
            f"\ntext_a = '{self.text_a}'" + \
            f"\ntext_b = '{self.text_b}'" + \
            f"\ntext_c = '{self.text_c}'"


class SearchableCollection:
    """
    Data class for storing a collection of `SearchableItem`.
    """
    def __init__(self, items: list[SearchableItem] | None = None):
        items = items or []
        self.items: dict[PositiveInt, SearchableItem] = {}

        try:
            iter(items)
        except TypeError:
            raise TypeError("Provided items are not iterable.")

        for item in items:
            if type(item) != SearchableItem: raise TypeError(f"Item {item} is not a <SearchableItem>.")
            if item.item_id is None: raise TypeError(f"Can't add `SearchableItem` without set `item_id`.")
            self.items[item.item_id] = item
    
    def __add__(self, x: "SearchableCollection") -> "SearchableCollection":
        if type(x) == SearchableCollection:
            result = SearchableCollection()
            
            for item in self.items.values():
                result.add_item(item)
            
            for item in x.items.values():
                result.add_item(item)
            
            return result
                        
        return NotImplemented
    
    def __len__(self) -> int:
        return len(self.items)
    
    def add_item(self, item: SearchableItem) -> None:
        """
        Adds a SearchableItem `item` to the collection. If item_id is already present in the collection, its data is concatenated.
        """
        if type(item) != SearchableItem: raise TypeError
        if item.item_id is None: raise TypeError(f"Can't add `SearchableItem` without set `item_id`.")

        if item.item_id in self.items:
            self.items[item.item_id] += item
        else:
            self.items[item.item_id] = item
    
    def serialize_for_insert(
            self,
            id_column_name: Literal["object_id", "tag_id"],
            modified_at: datetime
        ) -> list[dict[str, Any]]:
        """
        Serializes collection into a list of dictionaries
        with `id_name` as name of ID key and `modified_at` as value of corresponding table column.
        """
        return [
            Searchable.model_validate({
                f"{id_column_name}": i.item_id,
                "modified_at": modified_at,
                "text_a": i.text_a,
                "text_b": i.text_b,
                "text_c": i.text_c
            }).model_dump()
        for i in self.items.values()]


class Searchable(BaseModel):
    """
    Searchable attributes to be inserted into the database.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    object_id: PositiveInt | None = None
    tag_id: PositiveInt | None = None
    modified_at: datetime
    text_a: str
    text_b: str
    text_c: str


class MarkdownProcessingItem(BaseModel):
    """
    Data class for storing markdown data to be processed into a `SearchableItem`.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    id: PositiveInt
    raw_markdown: str


TextWeight = Literal["a", "b", "c"]
""" Text importancy weight in search results ordering. """
