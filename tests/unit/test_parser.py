# FILE: tests/unit/test_parser.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Юнит-тесты модуля M-PARSER (src/parser.py)
#   SCOPE: read_md, strip_frontmatter, get_frontmatter_title, md_to_html
#   DEPENDS: M-PARSER
#   LINKS: V-M-PARSER
#   ROLE: TEST
#   MAP_MODE: LOCALS
# END_MODULE_CONTRACT

import pytest
from src.parser import read_md, strip_frontmatter, get_frontmatter_title, md_to_html


class TestStripFrontmatter:
    def test_strips_yaml_frontmatter(self):
        text = "---\ntitle: Test\n---\nContent here"
        assert strip_frontmatter(text) == "Content here"

    def test_no_frontmatter_returns_as_is(self):
        text = "Just content"
        assert strip_frontmatter(text) == "Just content"

    def test_empty_frontmatter(self):
        text = "---\n---\nContent"
        assert strip_frontmatter(text) == "Content"


class TestGetFrontmatterTitle:
    def test_extracts_title(self):
        text = "---\ntitle: My Title\n---\nContent"
        assert get_frontmatter_title(text) == "My Title"

    def test_extracts_quoted_title(self):
        text = '---\ntitle: "Quoted Title"\n---\nContent'
        assert get_frontmatter_title(text) == "Quoted Title"

    def test_no_frontmatter_returns_none(self):
        assert get_frontmatter_title("No frontmatter") is None

    def test_no_title_in_frontmatter_returns_none(self):
        text = "---\nslug: /test\n---\nContent"
        assert get_frontmatter_title(text) is None


class TestReadMd:
    def test_existing_file(self):
        title, text = read_md("intro.md")
        assert title is not None
        assert text is not None
        assert len(text) > 0

    def test_nonexistent_file(self):
        title, text = read_md("nonexistent_file_xyz.md")
        assert title is None
        assert text is None


class TestMdToHtml:
    def test_paragraph(self):
        html = md_to_html("Hello **world**")
        assert "<strong>world</strong>" in html

    def test_table(self):
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        html = md_to_html(md)
        assert "<table>" in html

    def test_code_block(self):
        md = "```\nx = 1\n```"
        html = md_to_html(md)
        assert "<code>" in html

    def test_heading(self):
        html = md_to_html("## Test Heading")
        assert "<h2" in html and "Test Heading" in html
