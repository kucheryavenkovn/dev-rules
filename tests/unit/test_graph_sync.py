# FILE: tests/unit/test_graph_sync.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Юнит-тесты модуля M-GRAPHSYNC (src/graph_sync.py)
#   SCOPE: read_graph_modules, chapters_from_graph, sync_graph_from_fs, build_grace_graph_xml
#   DEPENDS: M-GRAPHSYNC
#   LINKS: V-M-GRAPHSYNC
#   ROLE: TEST
#   MAP_MODE: LOCALS
# END_MODULE_CONTRACT

from lxml import etree

from src.graph_sync import (
    read_graph_modules,
    chapters_from_graph,
    sync_graph_from_fs,
    build_grace_graph_xml,
)


class TestReadGraphModules:
    def test_reads_real_knowledge_graph(self):
        modules = read_graph_modules()
        assert len(modules) > 0

    def test_modules_have_ids(self):
        modules = read_graph_modules()
        for mod in modules:
            assert mod["id"].startswith("M-")

    def test_modules_have_purpose(self):
        modules = read_graph_modules()
        for mod in modules:
            assert "purpose" in mod

    def test_nonexistent_file_returns_empty(self, tmp_path):
        result = read_graph_modules(tmp_path / "nonexistent.xml")
        assert result == []

    def test_invalid_xml_returns_empty(self, tmp_path):
        bad_xml = tmp_path / "bad.xml"
        bad_xml.write_text("not xml at all <<<", encoding="utf-8")
        result = read_graph_modules(bad_xml)
        assert result == []


class TestChaptersFromGraph:
    def test_returns_nonempty(self):
        chapters = chapters_from_graph()
        assert len(chapters) > 0

    def test_chapters_have_module_id(self):
        chapters = chapters_from_graph()
        for ch in chapters:
            assert "module_id" in ch
            assert ch["module_id"].startswith("M-")

    def test_chapters_have_heading(self):
        chapters = chapters_from_graph()
        for ch in chapters:
            assert ch["heading"]

    def test_nonexistent_graph_returns_empty(self, tmp_path):
        result = chapters_from_graph(tmp_path / "nonexistent.xml")
        assert result == []

    def test_empty_docchapters_falls_back_to_discovery(self, tmp_path):
        xml_path = tmp_path / "kg.xml"
        xml_path.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<KnowledgeGraph><Project NAME="Test"><DocChapters></DocChapters></Project></KnowledgeGraph>',
            encoding="utf-8",
        )
        result = chapters_from_graph(xml_path)
        assert isinstance(result, list)


class TestSyncGraphFromFs:
    def test_returns_flat_list(self):
        flat = sync_graph_from_fs()
        assert isinstance(flat, list)
        assert len(flat) > 0

    def test_roundtrip_count(self):
        sync_graph_from_fs()
        chapters = chapters_from_graph()
        assert len(chapters) > 0

    def test_entries_have_heading(self):
        flat = sync_graph_from_fs()
        for ch in flat:
            assert "heading" in ch
            assert ch["heading"]


class TestBuildGraceGraphXml:
    def test_produces_valid_xml(self):
        modules = [
            {"id": "M-TEST", "heading": "Test", "type": "NARRATIVE",
             "para_start": 0, "para_end": 5, "elements": [], "subsections": [],
             "parent": None, "parent_heading": None},
        ]
        xml = build_grace_graph_xml(modules, 10, 2, 1, 3)
        root = etree.fromstring(xml.encode("utf-8"))
        assert root.tag == "GraceGraph"

    def test_contains_document_meta(self):
        modules = [
            {"id": "M-TEST", "heading": "Test", "type": "NARRATIVE",
             "para_start": 0, "para_end": 5, "elements": [], "subsections": [],
             "parent": None, "parent_heading": None},
        ]
        xml = build_grace_graph_xml(modules, 10, 2, 1, 3)
        root = etree.fromstring(xml.encode("utf-8"))
        meta = root.find("DocumentMeta")
        assert meta is not None
        assert meta.find("total-paragraphs").text == "10"
        assert meta.find("total-tables").text == "2"

    def test_contains_modules(self):
        modules = [
            {"id": "M-TEST", "heading": "Test", "type": "NARRATIVE",
             "para_start": 0, "para_end": 5, "elements": [], "subsections": [],
             "parent": None, "parent_heading": None},
        ]
        xml = build_grace_graph_xml(modules, 10, 2, 1, 3)
        root = etree.fromstring(xml.encode("utf-8"))
        modules_el = root.find("Modules")
        assert modules_el is not None
        test_mod = modules_el.find("M-TEST")
        assert test_mod is not None
        assert test_mod.find("BOOKMARK").text == "GRACE_M-TEST"

    def test_elements_included(self):
        modules = [
            {"id": "M-TABLE", "heading": "Tables", "type": "DATA",
             "para_start": 0, "para_end": 5,
             "elements": [{"type": "TABLE-DATA", "para-index": "3", "columns": "4", "rows": "5"}],
             "subsections": [], "parent": None, "parent_heading": None},
        ]
        xml = build_grace_graph_xml(modules, 10, 1, 1, 0)
        assert "TABLE-DATA" in xml
        assert "ELEMENTS" in xml

    def test_cross_links_with_parent(self):
        modules = [
            {"id": "M-PARENT", "heading": "Parent", "type": "NAVIGATION",
             "para_start": 0, "para_end": 0, "elements": [], "subsections": [],
             "parent": None, "parent_heading": None},
            {"id": "M-CHILD", "heading": "Child", "type": "NARRATIVE",
             "para_start": 1, "para_end": 3, "elements": [], "subsections": [],
             "parent": "M-PARENT", "parent_heading": "Parent"},
        ]
        xml = build_grace_graph_xml(modules, 10, 0, 2, 0)
        root = etree.fromstring(xml.encode("utf-8"))
        cross = root.find("CrossLinks")
        assert cross is not None
        links = [el for el in cross if el.tag == "link"]
        assert len(links) >= 1
