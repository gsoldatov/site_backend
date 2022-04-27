"""
Processing of Markdown blocks.
"""
import xml.etree.ElementTree as etree

from markdown.inlinepatterns import InlineProcessor, HtmlInlineProcessor, HTML_RE, ENTITY_RE
from markdown.util import AtomicString


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


class PatchedHtmlInlineProcessor(HtmlInlineProcessor):
    """
    Patched *INLINE* raw HTML processor, which fully deletes tags and special characters from text instead of placing temporary placeholders.
    Text content is still kept.
    """
    def handleMatch(self, m, data):
        return "", m.start(0), m.end(0)
