"""
Utilities for markdown parsing.
"""
from urllib.parse import urlparse

from markdown import Markdown
from markdown.extensions.tables import TableExtension
from markdown.extensions.md_in_html import MarkdownInHtmlExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.util import HTML_PLACEHOLDER_RE

from backend_main.db_operations.searchables.data_classes import SearchableItem
from backend_main.db_operations.searchables.markdown.block_processing import BlockFormulaProcessor, PatchedOListProcessor, PatchedUListProcessor
from backend_main.db_operations.searchables.markdown.inline_processing import InlineFormulaProcessor, INLINE_FORMULA_RE, \
    PatchedHtmlInlineProcessor, HTML_RE, ENTITY_RE


def get_markdown_processor(item_id, important_weight, regular_weight):
    """
    Returns a new `Markdown` instance with additional extensions, formulae processors and custom output format.
    """
    md = SearchableMarkdown(item_id, important_weight, regular_weight,
        extensions=[
            MarkdownInHtmlExtension(), # nested Markdown inside HTML
            TableExtension(),          # table parsing
            FencedCodeExtension()      # code parsing functionality (enables language detection ("```lang"))
    ])

    return md


IMPORTANT_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6")


def URL_is_absolute(url):
    return bool(urlparse(url).netloc)


class SearchableMarkdown(Markdown):
    """
    Child class of Markdown processor. 
    Provides block & inline formula processing & text serialization into a `SearchableItem` instance.
    """
    def __init__(self, item_id, important_weight, regular_weight, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Additional params
        self.searchable_item = SearchableItem(item_id)
        self.item_attr_important = f"text_{important_weight}"
        self.item_attr_regular = f"text_{regular_weight}"

        # Replace serializer func set by parent's constructor
        self.serializer = self._serializer

        # Disable parsed text processing to avoid errors
        self.stripTopLevelTags = False

        # Setup block & inline formula parsing
        self.parser.blockprocessors.register(BlockFormulaProcessor(self.parser), "formula", 81)          # higher priority over code block processor
        self.inlinePatterns.register(InlineFormulaProcessor(INLINE_FORMULA_RE), "inline_formula", 191)   # higher priority over inline code processor

        # Setup patched ordered & unordered list parsing
        self.parser.blockprocessors.deregister("olist")
        self.parser.blockprocessors.deregister("ulist")
        self.parser.blockprocessors.register(PatchedOListProcessor(self.parser), "olist", 40)
        self.parser.blockprocessors.register(PatchedUListProcessor(self.parser), "ulist", 30)

        # Setup patched inline HTML processors
        self.inlinePatterns.deregister("html")
        self.inlinePatterns.deregister("entity")
        self.inlinePatterns.register(PatchedHtmlInlineProcessor(HTML_RE, self), "html", 90)
        self.inlinePatterns.register(PatchedHtmlInlineProcessor(ENTITY_RE, self), "entity", 80)
    
    def _serializer(self, element):
        """ 
        Serializes provided XML Element `element` into `SearchableItem`.
        """
        # Check how element should be procecced
        item_attr = self.item_attr_important if element.tag in IMPORTANT_TAGS else self.item_attr_regular
        process_inner_content = not (
            element.tag == "code"
            or (element.tag == "p" and element.get("is_block_formula"))
            or (element.tag == "span" and element.get("is_inline_formula"))
        )

        # Process text before child elements
        if element.text and process_inner_content:
            self.searchable_item += {item_attr: SearchableMarkdown.remove_html_placeholders(element.text)}
        
        # Process URLs from <a> tags
        if element.tag == "a":
            if URL_is_absolute(element.get("href")):
                self.searchable_item += {item_attr: element.get("href")}

        # Process child elements 
        if process_inner_content:
            for sub in element:
                self.serializer(sub)
        
        # Process text after child elements
        if element.tail:
            self.searchable_item += {item_attr: SearchableMarkdown.remove_html_placeholders(element.tail)}
        
        # Return empty text for further processing by markdown lib
        return ""
    
    def remove_html_placeholders(s):
        return HTML_PLACEHOLDER_RE.sub("", s)
