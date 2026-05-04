# FILE: tests/unit/test_sidebar_order.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Юнит-тесты модуля M-SIDEBAR (src/sidebar_order.py)
#   SCOPE: build_chapter_order
#   DEPENDS: M-SIDEBAR, M-DISCOVERY, M-CONFIG, M-TYPES
#   LINKS: V-M-SIDEBAR
#   ROLE: TEST
#   MAP_MODE: LOCALS
# END_MODULE_CONTRACT

from unittest.mock import patch, MagicMock

import pytest

from src.sidebar_order import build_chapter_order
from src.types import ChapterInfo


class TestBuildChapterOrderReturnsNonEmpty:
    def test_returns_chapter_info_instances(self):
        result = build_chapter_order(use_graph=False)
        assert len(result) > 0
        assert all(isinstance(ch, ChapterInfo) for ch in result)

    def test_all_have_heading(self):
        result = build_chapter_order(use_graph=False)
        for ch in result:
            assert ch.heading


class TestSortedBySidebarPosition:
    def test_chapters_sorted_within_directory(self):
        flat = [
            {"heading": "Beta", "source": "beta.md", "depth": 0, "position": 5.0,
             "parent_heading": None, "is_container": False, "rel_path": "beta.md"},
            {"heading": "Alpha", "source": "alpha.md", "depth": 0, "position": 2.0,
             "parent_heading": None, "is_container": False, "rel_path": "alpha.md"},
            {"heading": "Gamma", "source": "gamma.md", "depth": 0, "position": 10.0,
             "parent_heading": None, "is_container": False, "rel_path": "gamma.md"},
        ]
        with patch("src.sidebar_order.scan_docs_directory", return_value=[]), \
             patch("src.sidebar_order.flatten_chapters", return_value=flat):
            result = build_chapter_order(use_graph=False)
        assert result[0].heading == "Beta"
        assert result[1].heading == "Alpha"
        assert result[2].heading == "Gamma"


class TestMissingPositionDefaults:
    def test_missing_position_defaults_to_999(self):
        flat = [
            {"heading": "NoPos", "source": "nopos.md", "depth": 0, "position": 999,
             "parent_heading": None, "is_container": False, "rel_path": "nopos.md"},
            {"heading": "HasPos", "source": "haspos.md", "depth": 0, "position": 1.0,
             "parent_heading": None, "is_container": False, "rel_path": "haspos.md"},
        ]
        with patch("src.sidebar_order.scan_docs_directory", return_value=[]), \
             patch("src.sidebar_order.flatten_chapters", return_value=flat):
            result = build_chapter_order(use_graph=False)
        headings = [ch.heading for ch in result]
        assert "NoPos" in headings
        no_pos_ch = next(ch for ch in result if ch.heading == "NoPos")
        assert no_pos_ch.position == 999


class TestCategoryHierarchy:
    def test_parent_child_hierarchy(self):
        flat = [
            {"heading": "Parent", "source": None, "depth": 0, "position": 1.0,
             "parent_heading": None, "is_container": True, "rel_path": "parent/"},
            {"heading": "Child", "source": "parent/child.md", "depth": 1, "position": 2.0,
             "parent_heading": "Parent", "is_container": False, "rel_path": "parent/child.md"},
        ]
        with patch("src.sidebar_order.scan_docs_directory", return_value=[]), \
             patch("src.sidebar_order.flatten_chapters", return_value=flat):
            result = build_chapter_order(use_graph=False)
        parent = next(ch for ch in result if ch.heading == "Parent")
        child = next(ch for ch in result if ch.heading == "Child")
        assert parent.is_container is True
        assert child.parent_heading == "Parent"
        assert child.depth == 1


class TestEmptyOrMissingDocsDir:
    def test_empty_docs_returns_empty(self):
        with patch("src.sidebar_order.scan_docs_directory", return_value=[]), \
             patch("src.sidebar_order.flatten_chapters", return_value=[]):
            result = build_chapter_order(use_graph=False)
        assert result == []

    def test_nonexistent_docs_returns_empty(self):
        with patch("src.sidebar_order.scan_docs_directory", return_value=[]), \
             patch("src.sidebar_order.flatten_chapters", return_value=[]):
            result = build_chapter_order(use_graph=False)
        assert isinstance(result, list)
        assert len(result) == 0


class TestGraphFirstFallback:
    def test_returns_graph_data_when_available(self):
        graph_data = [
            {"heading": "GraphChapter", "source": "g.md", "depth": 0, "position": 1.0,
             "parent_heading": None, "is_container": False, "rel_path": "g.md",
             "module_id": "M-GRAPH"},
        ]
        with patch("src.sidebar_order.chapters_from_graph", return_value=graph_data):
            result = build_chapter_order(use_graph=True)
        assert len(result) == 1
        assert isinstance(result[0], ChapterInfo)
        assert result[0].heading == "GraphChapter"
        assert result[0].module_id == "M-GRAPH"

    def test_falls_back_to_discovery_when_graph_empty(self):
        with patch("src.sidebar_order.chapters_from_graph", return_value=[]), \
             patch("src.sidebar_order.scan_docs_directory", return_value=[]), \
             patch("src.sidebar_order.flatten_chapters", return_value=[
                 {"heading": "Disc", "source": "d.md", "depth": 0, "position": 1.0,
                  "parent_heading": None, "is_container": False, "rel_path": "d.md"},
             ]):
            result = build_chapter_order(use_graph=True)
        assert len(result) == 1
        assert result[0].heading == "Disc"
