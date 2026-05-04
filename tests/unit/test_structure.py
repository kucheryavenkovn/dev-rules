# FILE: tests/unit/test_structure.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Юнит-тесты модуля M-STRUCTURE (src/structure.py)
#   SCOPE: collect_chapters
#   DEPENDS: M-STRUCTURE
#   LINKS: V-M-STRUCTURE
#   ROLE: TEST
#   MAP_MODE: LOCALS
# END_MODULE_CONTRACT

import pytest
from collections import OrderedDict
from src.structure import collect_chapters


class TestCollectChapters:
    def test_flat_dict(self):
        chapters = OrderedDict([("A", "a.md"), ("B", "b.md")])
        result = collect_chapters(chapters)
        assert len(result) == 2
        assert result[0]["heading"] == "A"
        assert result[0]["source"] == "a.md"
        assert result[0]["depth"] == 0

    def test_nested_dict(self):
        chapters = OrderedDict([
            ("Root", OrderedDict([
                ("Child1", "c1.md"),
                ("Child2", "c2.md"),
            ])),
        ])
        result = collect_chapters(chapters)
        assert len(result) == 3
        assert result[0]["is_container"] is True
        assert result[0]["depth"] == 0
        assert result[1]["depth"] == 1
        assert result[1]["parent_id"] == "Root"

    def test_deeply_nested(self):
        chapters = OrderedDict([
            ("L0", OrderedDict([
                ("L1", OrderedDict([
                    ("L2", "leaf.md"),
                ])),
            ])),
        ])
        result = collect_chapters(chapters)
        assert result[2]["depth"] == 2
        assert result[2]["source"] == "leaf.md"

    def test_default_uses_chapters(self):
        result = collect_chapters()
        assert len(result) > 0
        assert all("heading" in ch for ch in result)

    def test_container_has_no_source(self):
        chapters = OrderedDict([
            ("Container", OrderedDict([("Leaf", "leaf.md")])),
        ])
        result = collect_chapters(chapters)
        assert result[0]["source"] is None
        assert result[0]["is_container"] is True
        assert result[1]["source"] == "leaf.md"
