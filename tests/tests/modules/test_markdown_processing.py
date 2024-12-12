"""
Tests for Markdown processing into text.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 4)))
    from tests.util import run_pytest_tests

from backend_main.db_operations.searchables.markdown import markdown_to_searchable_item


def test_item_id_and_weights():
    # Process with set id and weights
    si = markdown_to_searchable_item("# Header\nText", item_id=100, important_weight="b", regular_weight="c")
    assert si.item_id == 100
    assert si.text_a == ""
    assert si.text_b.find("Header") != -1
    assert si.text_c.find("Text") != -1

    # Process with default id and weights
    si = markdown_to_searchable_item("# Header\nText")
    assert si.item_id is None
    assert si.text_a.find("Header") != -1
    assert si.text_b.find("Text") != -1
    assert si.text_c == ""


def test_raw_text():
    si = markdown_to_searchable_item("First \n\n Second Second2 \n\n Third")
    assert str_to_list_of_alphanum_words(si.text_b) == ["First", "Second", "Second2", "Third"]


def test_headers():
    # Process with set id and weights
    text = "".join(("#" * i + f" Header{i} \n" + f"Para{i} \n" for i in range(1, 7)))
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_a) == [f"Header{i}" for i in range(1, 7)]
    assert str_to_list_of_alphanum_words(si.text_b) == [f"Para{i}" for i in range(1, 7)]


def test_ordered_lists():
    # List at the beginning of a paragraph
    text = "para1 \n\n" + "1. item1 \n" + "2. item2 \n" + "    1. item21 \n" + "3. item3 \n\n" + "para2"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["para1", "item1", "item2", "item21", "item3", "para2"]

    # List after a paragraph without double newline separator
    # NOTE: default backend & frontend Markdown parsers behave differently here: 
    # frontend renders the list, while backend appends it to the existing paragraph.
    # This case should be handled by the patched processor in the same way, as it's done in the frontend.
    text = "para1 \n" + "1. item1 \n" + "2. item2 \n" + "    1. item21 \n" + "3. item3 \n\n" + "para2"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["para1", "item1", "item2", "item21", "item3", "para2"]

    # List after a code block without double newline separator
    # This case should be handled by the patched processor in the same way, as it's done in the frontend.
    text = "``` \n code \n ``` \n" + "1. item1 \n" + "2. item2 \n" + "    1. item21 \n" + "3. item3 \n\n" + "para2"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["item1", "item2", "item21", "item3", "para2"]

    # List after a header without double newline separator
    # This case should be handled by the patched processor in the same way, as it's done in the frontend.
    text = "# Header \n" + "1. item1 \n" + "2. item2 \n" + "    1. item21 \n" + "3. item3 \n\n" + "para2"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["item1", "item2", "item21", "item3", "para2"]


def test_unordered_lists():
    # List at the beginning of a paragraph
    text = "para1 \n\n" + "- item1 \n" + "- item2 \n" + "    - item21 \n" + "- item3 \n\n" + "para2"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["para1", "item1", "item2", "item21", "item3", "para2"]

    # List after a paragraph without double newline separator
    # NOTE: backend & frontend Markdown parsers behave differently here: 
    # frontend renders the list, while backend appends it to the existing paragraph.
    # This case should be handled by the patched processor in the same way, as it's done in the frontend.
    text = "para1 \n" + "- item1 \n" + "- item2 \n" + "    - item21 \n" + "- item3 \n\n" + "para2"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["para1", "item1", "item2", "item21", "item3", "para2"]

    # List after a code block without double newline separator
    # This case should be handled by the patched processor in the same way, as it's done in the frontend.
    text = "``` \n code \n ``` \n" + "- item1 \n" + "- item2 \n" + "    - item21 \n" + "- item3 \n\n" + "para2"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["item1", "item2", "item21", "item3", "para2"]

    # List after a header without double newline separator
    # This case should be handled by the patched processor in the same way, as it's done in the frontend.
    text = "# Header \n" + "- item1 \n" + "- item2 \n" + "    - item21 \n" + "- item3 \n\n" + "para2"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["item1", "item2", "item21", "item3", "para2"]


def test_nested_lists():
    # List after a paragraph without double newline separator
    # NOTE: backend & frontend Markdown parsers behave differently here: 
    # frontend renders the list, while backend appends it to the existing paragraph.
    # This case should be handled by the patched processor in the same way, as it's done in the frontend.
    text = "para1 \n" + "1. item1 \n" + "2. item2 \n" + "    - item21 \n" + "3. item3 \n\n" + "para2"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["para1", "item1", "item2", "item21", "item3", "para2"]


def test_table():
    text = "para1 \n\n col1 | col2 | col3 \n  ----- | ------ | ----- \n  txt1 | txt2 | txt3 \n\n  para2"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["para1", "col1", "col2", "col3", "txt1", "txt2", "txt3", "para2"]


def test_quotes():
    # Quote after a paragraph without double newline separation
    text = "para1 \n > quote \n\n para2"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["para1", "quote", "para2"]

    # Nested quote
    text = "para1 \n > first1 \n > > second \n > \n > first2 \n\n para2"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["para1", "first1", "second", "first2", "para2"]


def test_quotes():
    # Link with an absolute URL
    text = "para1 [link text](https://google.com) para2"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["para1", "link", "text", keep_alnum("https://google.com"), "para2"]
    
    # Link with a relative URL
    text = "para1 [link text](/relative1#someID) para2"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["para1", "link", "text", "para2"]


def test_block_code():
    # Block code with a specified language & no double newline separation
    text = "para1 \n ```python \n code \n ``` \n para2"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["para1", "para2"]


def test_inline_code():
    text = "para1 `code` para2"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["para1", "para2"]


def test_block_formulae():
    # Correct formula between paragraphs with two newline separators
    text = "para1 \n\n$$ \n formula \n $$ \n para2"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["para1", "para2"]

    # Unclosed formulae
    for open, close in [("$$", "$"), ("$$", "")]:
            text = "para1 \n\n{} \n formula \n {}".format(open, close)
            si = markdown_to_searchable_item(text)
            assert str_to_list_of_alphanum_words(si.text_b) == ["para1", "formula"]
    
    # Escaped opening & closing dollar-signs
    for open, close in [("\\$$", "$$"), ("$\\$", "$$"), ("$$", "\\$$"), ("$$", "$\\$")]:
            text = "para1 \n\n{} \n formula \n {}".format(open, close)
            si = markdown_to_searchable_item(text)
            assert str_to_list_of_alphanum_words(si.text_b) == ["para1", "formula"]
    
    # Escaped dollar-sign inside formula
    text = "para1 \n\n$$ \n formula \\$ \n $$\n para2"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["para1", "para2"]
    
    # Correct formula in the middle of a paragraph line
    for separator in ("\n", ""):
        text = "para1 {}$$ \n formula \n $$ \n para2".format(separator)
        si = markdown_to_searchable_item(text)
        assert str_to_list_of_alphanum_words(si.text_b) == ["para1", "formula", "para2"]


def test_inline_formulae():
    # Correct formula in the middle of a paragraph
    text = "before $ formula $ after"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["before", "after"]

    # Escaped opening & closing dollar signs
    for open, close in [("\\$", "$"), ("$", "\\$")]:
        text = "before {} formula {} after".format(open, close)
        si = markdown_to_searchable_item(text)
        assert str_to_list_of_alphanum_words(si.text_b) == ["before", "formula", "after"]
    
    # Escaped dollar sign in the formula
    text = "before $ formula \\$ $ after"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["before", "after"]


def test_raw_html():
    # Block HTML
    text = "para1 \n\n <p> para2 </p> \n\n para3"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["para1", "para3"]

    # Inline HTML
    # Currently allows inner text to be processed as well
    text = "first <span> inline </span> second"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["first", "inline", "second"]
    
    # HTML special chars
    text = "first <span> &quot; inline </span> second"
    si = markdown_to_searchable_item(text)
    assert str_to_list_of_alphanum_words(si.text_b) == ["first", "inline", "second"]


def str_to_list_of_alphanum_words(text):
    """ Splits string into a list or words and strips the words. Returns the array of non-empty word strings. """
    m = map(keep_alnum, text.split(" "))
    f = filter(lambda s: len(s) > 0, m)
    return list(f)


def keep_alnum(s):
    return "".join(c for c in s if c.isalnum())


if __name__ == "__main__":
    run_pytest_tests(__file__)
