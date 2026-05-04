# FILE: tests/unit/test_config.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Юнит-тесты модуля M-CONFIG (src/config.py)
#   SCOPE: derive_module_id, classify_module_type, CHAPTERS
#   DEPENDS: M-CONFIG
#   LINKS: V-M-CONFIG
#   ROLE: TEST
#   MAP_MODE: LOCALS
# END_MODULE_CONTRACT

import pytest
from docx import Document

from src.config import (
    derive_module_id,
    classify_module_type,
    setup_styles,
    DOC_NAME,
    DOC_VERSION,
    GRACE_VERSION,
)


class TestDeriveModuleId:
    def test_known_heading_returns_predefined_id(self):
        assert derive_module_id("Введение", set()) == "M-INTRO"

    def test_another_known_heading(self):
        assert derive_module_id("Запросы", set()) == "M-QUERY"

    def test_duplicate_id_gets_suffix(self):
        existing = {"M-OVERVIEW"}
        result = derive_module_id("Обзор", existing)
        assert result == "M-OVERVIEW-2"

    def test_unknown_heading_returns_latin_id(self):
        result = derive_module_id("SomeNewSection", set())
        assert result.startswith("M-")
        assert result.isascii() or all(c.isalnum() or c == "-" for c in result[2:])

    def test_no_cyrillic_in_id(self):
        result = derive_module_id("Новая секция", set())
        for c in result:
            assert ord(c) < 128, f"Cyrillic character found in ID: {result}"

    def test_uniqueness_across_many_calls(self):
        headings = ["Обзор"] * 10
        ids = set()
        for h in headings:
            mid = derive_module_id(h, ids)
            ids.add(mid)
        assert len(ids) == 10

    def test_all_special_ids_are_latin(self):
        from src.config import _MODULE_ID_SPECIAL
        for heading, mid in _MODULE_ID_SPECIAL.items():
            for c in mid:
                assert ord(c) < 128, f"Non-ASCII in {mid} for heading '{heading}'"


class TestClassifyModuleType:
    def test_prose_only_is_narrative(self):
        assert classify_module_type("<p>Hello</p>") == "NARRATIVE"

    def test_code_only_is_narrative(self):
        assert classify_module_type("<pre><code>x = 1</code></pre>") == "NARRATIVE"

    def test_table_only_is_data(self):
        assert classify_module_type("<table><tr><td>1</td></tr></table>") == "DATA"

    def test_mixed_table_code_prose(self):
        html = "<p>text</p><table><tr><td>1</td></tr></table><code>x</code>"
        assert classify_module_type(html) == "MIXED"

    def test_empty_is_narrative(self):
        assert classify_module_type("") == "NARRATIVE"


class TestSetupStyles:
    def test_does_not_crash(self):
        doc = Document()
        setup_styles(doc)
        assert "Normal" in [s.name for s in doc.styles]

    def test_code_style_created(self):
        doc = Document()
        setup_styles(doc)
        assert "Code" in [s.name for s in doc.styles]


class TestDiscoveryIntegration:
    def test_discovery_finds_chapters(self):
        from src.discovery import scan_docs_directory, flatten_chapters
        nodes = scan_docs_directory()
        flat = flatten_chapters(nodes)
        assert len(flat) > 0

    def test_first_discovered_is_intro(self):
        from src.discovery import scan_docs_directory
        nodes = scan_docs_directory()
        md_nodes = [n for n in nodes if n.source and "intro" in n.source]
        assert len(md_nodes) >= 1
