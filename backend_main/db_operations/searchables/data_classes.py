class SearchableItem:
    """
    Data class for accumulating searchable text of an item.
    Stores item ID and searchable texts of A, B & C search weight levels.
    """
    def __init__(self, item_id = None, text_a = "", text_b = "", text_c = ""):
        self.item_id = item_id
        self.text_a = text_a
        self.text_b = text_b
        self.text_c = text_c
    
    def __add__(self, x):
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
    
    def __str__(self):
        return f"<SearchableItem id = {self.item_id}>" + \
            f"\ntext_a = '{self.text_a}'" + \
            f"\ntext_b = '{self.text_b}'" + \
            f"\ntext_c = '{self.text_c}'"



class SearchableCollection:
    """
    Data class for storing a collection of `SearchableItem`.
    """
    def __init__(self, items = []):
        self.items = {}

        try:
            iter(items)
        except TypeError:
            raise TypeError("Provided items are not iterable.")

        for item in items:
            if type(item) != SearchableItem: raise TypeError(f"Item {item} is not a <SearchableItem>.")
            self.items[item.item_id] = item
    
    def __add__(self, x):
        if type(x) == SearchableCollection:
            result = SearchableCollection()
            
            for item in self.items.values():
                result.add_item(item)
            
            for item in x.items.values():
                result.add_item(item)
            
            return result
                        
        return NotImplemented
    
    def __len__(self):
        return len(self.items)
    
    def add_item(self, item):
        """
        Adds a SearchableItem `item` to the collection. If item_id is already present in the collection, its data is concatenated.
        """
        if type(item) != SearchableItem: raise TypeError

        if item.item_id in self.items:
            self.items[item.item_id] += item
        else:
            self.items[item.item_id] = item
