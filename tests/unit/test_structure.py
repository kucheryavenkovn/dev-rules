# FILE: tests/unit/test_structure.py
# VERSION: 1.0.1
# START_MODULE_CONTRACT
#   PURPOSE: Юнит-тесты модуля M-STRUCTURE (src/structure.py)
#   SCOPE: collect_chapters
#   DEPENDS: M-STRUCTURE, M-DISCOVERY
#   LINKS: V-M-STRUCTURE
#   ROLE: TEST
#   MAP_MODE: LOCALS
# END_MODULE_CONTRACT

import pytest
from src.structure import collect_chapters
from src.discovery import flatten_chapters, scan_docs_directory, ChapterNode


class TestCollectChapters:
    def test_default_returns_nonempty(self):
        result = collect_chapters()
        assert len(result) > 0

    def test_all_entries_have_heading(self):
        result = collect_chapters()
        for ch in result:
            assert "heading" in ch
            assert ch["heading"]

    def test_all_entries_have_module_id(self):
        result = collect_chapters()
        for ch in result:
            assert "module_id" in ch
            assert ch["module_id"].startswith("M-")

    def test_module_ids_unique(self):
        result = collect_chapters()
        ids = [ch["module_id"] for ch in result]
        assert len(ids) == len(set(ids))

    def test_module_ids_all_latin(self):
        result = collect_chapters()
        for ch in result:
            for c in ch["module_id"]:
                assert ord(c) < 128, f"Non-ASCII in {ch['module_id']}"


class TestDiscoveryFlat:
    def test_flatten_empty(self):
        assert flatten_chapters([]) == []

    def test_flatten_single_leaf(self):
        nodes = [ChapterNode(heading="Test", source="test.md", position=1)]
        result = flatten_chapters(nodes)
        assert len(result) == 1
        assert result[0]["heading"] == "Test"

    def test_flatten_nested(self):
        child = ChapterNode(heading="Child", source="child.md", position=1, depth=1)
        parent = ChapterNode(heading="Parent", position=0, depth=0, is_container=True, children=[child])
        result = flatten_chapters([parent])
        assert len(result) == 2
        assert result[0]["heading"] == "Parent"
        assert result[1]["heading"] == "Child"
        assert result[1]["parent_heading"] == "Parent"

    def test_scan_docs_finds_files(self):
        nodes = scan_docs_directory()
        assert len(nodes) > 0
        all_flat = flatten_chapters(nodes)
        assert len(all_flat) > 10
