# FILE: tests/unit/test_types.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Юнит-тесты для M-TYPES: ChapterInfo, ModuleInfo, GraceModule
#   SCOPE: Конструкция, иммутабельность, сериализация
#   DEPENDS: M-TYPES
#   LINKS: V-M-TYPES
#   ROLE: TEST
#   MAP_MODE: EXPORTS
# END_MODULE_CONTRACT

import pytest
from dataclasses import FrozenInstanceError

from src.types import ChapterInfo, ModuleInfo, GraceModule


class TestChapterInfo:

    def test_construction_with_all_fields(self):
        ch = ChapterInfo(
            heading="Test Chapter",
            source="test.md",
            depth=1,
            position=2.0,
            parent_heading="Parent",
            is_container=False,
            rel_path="test.md",
            module_id="M-TEST",
        )
        assert ch.heading == "Test Chapter"
        assert ch.source == "test.md"
        assert ch.depth == 1
        assert ch.position == 2.0
        assert ch.parent_heading == "Parent"
        assert ch.is_container is False
        assert ch.rel_path == "test.md"
        assert ch.module_id == "M-TEST"

    def test_construction_with_defaults(self):
        ch = ChapterInfo(heading="Hello")
        assert ch.heading == "Hello"
        assert ch.source is None
        assert ch.depth == 0
        assert ch.position == 0.0
        assert ch.parent_heading is None
        assert ch.is_container is False
        assert ch.rel_path == ""
        assert ch.module_id is None

    def test_frozen_immutability(self):
        ch = ChapterInfo(heading="Immutable")
        with pytest.raises(FrozenInstanceError):
            ch.heading = "Changed"

    def test_to_dict(self):
        ch = ChapterInfo(heading="Dict Test", source="a.md", depth=2, module_id="M-DICT")
        d = ch.to_dict()
        assert d["heading"] == "Dict Test"
        assert d["source"] == "a.md"
        assert d["depth"] == 2
        assert d["module_id"] == "M-DICT"
        assert d["parent_heading"] is None

    def test_from_dict(self):
        d = {"heading": "From Dict", "source": "b.md", "depth": 3, "position": 5.0}
        ch = ChapterInfo.from_dict(d)
        assert ch.heading == "From Dict"
        assert ch.source == "b.md"
        assert ch.depth == 3
        assert ch.position == 5.0

    def test_from_dict_roundtrip(self):
        original = ChapterInfo(heading="Round", source="c.md", position=1.5, is_container=True, module_id="M-RT")
        d = original.to_dict()
        restored = ChapterInfo.from_dict(d)
        assert restored == original

    def test_with_module_id(self):
        ch = ChapterInfo(heading="Test")
        ch2 = ch.with_module_id("M-NEW")
        assert ch.module_id is None
        assert ch2.module_id == "M-NEW"
        assert ch.heading == ch2.heading

    def test_equality(self):
        a = ChapterInfo(heading="Same", position=1.0)
        b = ChapterInfo(heading="Same", position=1.0)
        assert a == b

    def test_hash(self):
        a = ChapterInfo(heading="Hash", position=1.0)
        b = ChapterInfo(heading="Hash", position=1.0)
        assert hash(a) == hash(b)
        assert len({a, b}) == 1


class TestModuleInfo:

    def test_construction_with_all_fields(self):
        mi = ModuleInfo(
            id="M-TEST",
            heading="Test Module",
            type="DATA",
            para_start=10,
            para_end=20,
            elements=({"type": "TABLE-DATA"},),
            subsections=(),
            parent="M-PARENT",
            parent_heading="Parent",
        )
        assert mi.id == "M-TEST"
        assert mi.heading == "Test Module"
        assert mi.type == "DATA"
        assert mi.para_start == 10
        assert mi.para_end == 20
        assert len(mi.elements) == 1
        assert mi.parent == "M-PARENT"

    def test_construction_with_defaults(self):
        mi = ModuleInfo(id="M-DEF", heading="Default")
        assert mi.type == "NARRATIVE"
        assert mi.para_start == 0
        assert mi.para_end == 0
        assert mi.elements == ()
        assert mi.subsections == ()
        assert mi.parent is None

    def test_frozen_immutability(self):
        mi = ModuleInfo(id="M-FRZ", heading="Frozen")
        with pytest.raises(FrozenInstanceError):
            mi.heading = "Changed"

    def test_to_dict(self):
        mi = ModuleInfo(id="M-D", heading="Dict", elements=({"type": "TABLE"},))
        d = mi.to_dict()
        assert d["id"] == "M-D"
        assert isinstance(d["elements"], list)
        assert len(d["elements"]) == 1

    def test_from_dict(self):
        d = {"id": "M-F", "heading": "From", "type": "MIXED", "elements": [{"type": "X"}]}
        mi = ModuleInfo.from_dict(d)
        assert mi.id == "M-F"
        assert mi.type == "MIXED"
        assert isinstance(mi.elements, tuple)

    def test_from_dict_roundtrip(self):
        original = ModuleInfo(id="M-RT", heading="RT", type="DATA", para_start=5, para_end=10)
        d = original.to_dict()
        restored = ModuleInfo.from_dict(d)
        assert restored == original


class TestGraceModule:

    def test_construction(self):
        gm = GraceModule(
            id="M-GR",
            heading="Grace Module",
            type="NARRATIVE",
            bookmark="GRACE_M-GR",
            para_start=0,
            para_end=5,
        )
        assert gm.id == "M-GR"
        assert gm.bookmark == "GRACE_M-GR"
        assert gm.para_start == 0
        assert gm.para_end == 5

    def test_construction_defaults(self):
        gm = GraceModule(id="M-G", heading="G", type="DATA", bookmark="GRACE_M-G")
        assert gm.para_start == 0
        assert gm.para_end == 0
        assert gm.elements == ()

    def test_frozen_immutability(self):
        gm = GraceModule(id="M-F", heading="F", type="NARRATIVE", bookmark="GRACE_M-F")
        with pytest.raises(FrozenInstanceError):
            gm.heading = "Changed"

    def test_to_dict(self):
        gm = GraceModule(id="M-TD", heading="TD", type="MIXED", bookmark="GRACE_M-TD")
        d = gm.to_dict()
        assert d["id"] == "M-TD"
        assert d["bookmark"] == "GRACE_M-TD"
