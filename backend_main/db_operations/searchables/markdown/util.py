"""
Utilities for markdown parsing.
"""
import re
from urllib.parse import urlparse
import xml.etree.ElementTree as etree

from markdown import Markdown
from markdown.extensions.tables import TableExtension
from markdown.extensions.md_in_html import MarkdownInHtmlExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.blockprocessors import BlockProcessor
from markdown.inlinepatterns import InlineProcessor
from markdown.util import AtomicString

from backend_main.db_operations.searchables.data_classes import SearchableItem


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


class BlockFormulaProcessor(BlockProcessor):
    """ 
    Block formulae processor.
    """

    # RE = re.compile(r"\$\$((\\\$|[^\$])+?)\$\$") # not catching escaped dollar-sign at the beginning
    # RE = re.compile(r"[^\\|\^]\$\$((\\\$|[^\$])+?)\$\$") # working, including 1 excess symbols at the start
    # RE = re.compile(r"(?<!\\)\$\$((\\\$|[^\$])+?)\$\$")  # wrong processing for $$...\$$ case
    RE = re.compile(r"(?<!\\)\$\$([^\$]+)(?<!\\)\$\$")
    # TODO block formula must be at the beginning of the block

    def test(self, parent, block):
        """ Checks text `block` for the presence of a formula. """
        return bool(self.RE.search(block))
    
    def run(self, parent, blocks):
        """ Gets the first block from `blocks` list with the block-formula, parses the texts before & after the block and the formula. """
        block = blocks.pop(0)
        m = self.RE.search(block)

        if m:
            before = block[:m.start()]
            after = block[m.end():]

            # Process symblos before formula
            if before: self.parser.parseBlocks(parent, [before])

            # Create formula paragraph
            p = etree.SubElement(parent, "p")
            p.text = AtomicString(m.group(1))
            p.set("is_block_formula", "true")
            
            # Insert remaining lines as first block for future parsing.
            if after: blocks.insert(0, after)


# INLINE_FORMULA_RE = r"[^\\|\^]\$((\\\$|[^\$\n])+)\$"  # doesn't exclude pattern preceded by backslash
# INLINE_FORMULA_RE = r"([^\\]|^)\$((\\\$|[^\$\n])+)\$" # doesn't exclude escaped ending dollar-sign
INLINE_FORMULA_RE = r"(?<!\\)\$((\\\$|[^\$\n])+)(?<!\\)\$"

    
class InlineFormulaProcessor(InlineProcessor):
    """
    Inline formula processor.
    """
    def handleMatch(self, m, data):
        """ Generate element + start & end positions from the match in the string. """
        el = etree.Element("span")
        el.text = AtomicString(m.group(1))
        el.set("is_inline_formula", "true")

        # First symbol in the pattern can be a string start or a backslash
        # The latter should be left for further processing
        start = m.start(0) # + (1 if len(m.group(1)) > 0 else 0)

        return el, start, m.end(0)


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

        # Replace serializer func
        self.serializer = self._serializer

        # Disable parsed text processing
        self.stripTopLevelTags = False

        # Setup block & inline formula parsing
        self.parser.blockprocessors.register(BlockFormulaProcessor(self.parser), "formula", 81)          # higher priority over code block processor
        self.inlinePatterns.register(InlineFormulaProcessor(INLINE_FORMULA_RE), "inline_formula", 191)   # higher priority over inline code processor
    
    def _serializer(self, element):
        # Check how element should be procecced
        item_attr = self.item_attr_important if element.tag in IMPORTANT_TAGS else self.item_attr_regular
        process_inner_content = not (
            element.tag == "code"
            or (element.tag == "p" and element.get("is_block_formula"))
            or (element.tag == "span" and element.get("is_inline_formula"))
        )

        # Process text before child elements
        if element.text and process_inner_content:
            self.searchable_item += {item_attr: element.text}
        
        # Process URLs from <a> tags
        if element.tag == "a":
            if URL_is_absolute(element.href):
                self.searchable_item += {item_attr: element.href}

        # Process child elements 
        if process_inner_content:
            for sub in element:
                self.serializer(sub)
        
        # Process text after child elements
        if element.tail:
            self.searchable_item += {item_attr: element.tail}
        
        # Return empty text for further processing by markdown lib
        return ""
