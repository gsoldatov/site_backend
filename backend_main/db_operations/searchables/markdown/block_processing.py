"""
Processing of Markdown blocks.
"""
import re
import xml.etree.ElementTree as etree

from markdown.blockprocessors import BlockProcessor, OListProcessor
from markdown.util import AtomicString


class BlockFormulaProcessor(BlockProcessor):
    """ 
    Block formulae processor.
    """
    # RE = re.compile(r"\$\$((\\\$|[^\$])+?)\$\$") # not catching escaped dollar-sign at the beginning
    # RE = re.compile(r"[^\\|\^]\$\$((\\\$|[^\$])+?)\$\$") # working, including 1 excess symbols at the start
    # RE = re.compile(r"(?<!\\)\$\$((\\\$|[^\$])+?)\$\$")  # wrong processing for $$...\$$ case
    # RE = re.compile(r"(?<!\\)\$\$([^\$]+)(?<!\\)\$\$")   # allows formulae not properly starting at the block beginning
    # RE = re.compile(r"^\$\$([^\$]+)(?<!\\)\$\$")         # always excepts string start at the beginning
    # RE = re.compile(r"(?:^|(?<=%s{2,2}))\$\$([^\$]+)(?<!\\)\$\$" % ("\n")) # does not allow escaped dollar signs inside the formulae

    RE = re.compile(r"(?:^|(?<=%s{2,2}))\$\$((\\\$|[^\$])+?)(?<!\\)\$\$" % ("\n"))

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


class PatchedOListProcessor(OListProcessor):
    """
    Patched default processor for ordered lists.
    Allows lists to start at the beginning of a new line, rather than just at the beginning of a block.
    """
    def __init__(self, parser):
        super().__init__(parser)
        # Default regex modified to allow newline before the match as well as string start
        # self.RE = re.compile(r"(?<=[\^|%s])[ ]{0,%d}\d+\.[ ]+(.*)" % ("\n", self.tab_length - 1))
        self.RE = re.compile(r"(?:^|(?<=%s))[ ]{0,%d}\d+\.[ ]+(.*)" % ("\n", self.tab_length - 1))
    
    def test(self, parent, block):
        """ Checks text `block` for the presence of a formula. """
        return bool(self.RE.search(block))
    
    def run(self, parent, blocks):
        """
        Processes the string part before the match as a separate block, then passes the remaining string with default processor
        """
        block = blocks.pop(0)
        m = self.RE.search(block)

        if m:
            before = block[:m.start()]

            # Process symblos before formula
            if before: self.parser.parseBlocks(parent, [before])

            # Process the list
            blocks.insert(0, block[m.start():])
            super().run(parent, blocks)


class PatchedUListProcessor(PatchedOListProcessor):
    TAG = "ul"

    def __init__(self, parser):
        super().__init__(parser)
        # Default regex modified to allow newline before the match as well as string start
        # self.RE = re.compile(r"(?<=[\^|%s])[ ]{0,%d}[*+-][ ]+(.*)" % ("\n", self.tab_length - 1))
        self.RE = re.compile(r"(?:^|(?<=%s))[ ]{0,%d}[*+-][ ]+(.*)" % ("\n", self.tab_length - 1))
