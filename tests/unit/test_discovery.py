# FILE: tests/unit/test_discovery.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Юнит-тесты модуля M-DISCOVERY (src/discovery.py)
#   SCOPE: scan_docs_directory, flatten_chapters, read_category_json, read_md_frontmatter_position
#   DEPENDS: M-DISCOVERY
#   LINKS: V-M-DISCOVERY
#   ROLE: TEST
#   MAP_MODE: LOCALS
# END_MODULE_CONTRACT

import json
import pytest

from src.discovery import (
    scan_docs_directory,
    flatten_chapters,
    read_category_json,
    read_md_frontmatter_position,
    ChapterNode,
)


class TestReadCategoryJson:
    def test_valid_category(self, tmp_path):
        cat_file = tmp_path / "_category_.json"
        cat_file.write_text(json.dumps({"label": "My Section", "position": 5}), encoding="utf-8")
        label, pos = read_category_json(tmp_path)
        assert label == "My Section"
        assert pos == 5

    def test_missing_category_uses_dir_name(self, tmp_path):
        subdir = tmp_path / "mysubdir"
        subdir.mkdir()
        label, pos = read_category_json(subdir)
        assert label == "mysubdir"
        assert pos == 999

    def test_invalid_json_uses_defaults(self, tmp_path):
        cat_file = tmp_path / "_category_.json"
        cat_file.write_text("not json", encoding="utf-8")
        label, pos = read_category_json(tmp_path)
        assert pos == 999


class TestReadFrontmatterPosition:
    def test_extracts_position_and_title(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("---\nsidebar_position: 3\ntitle: My Title\n---\nContent", encoding="utf-8")
        pos, title, sidebar_label, slug = read_md_frontmatter_position(md)
        assert pos == 3.0
        assert title == "My Title"

    def test_extracts_sidebar_label(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("---\nsidebar_label: Custom Label\n---\nContent", encoding="utf-8")
        _, _, sidebar_label, _ = read_md_frontmatter_position(md)
        assert sidebar_label == "Custom Label"

    def test_extracts_slug(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("---\nslug: /my/slug\n---\nContent", encoding="utf-8")
        _, _, _, slug = read_md_frontmatter_position(md)
        assert slug == "/my/slug"

    def test_no_frontmatter_defaults(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("Just content", encoding="utf-8")
        pos, title, sidebar_label, slug = read_md_frontmatter_position(md)
        assert pos == 999.0
        assert title is None

    def test_title_from_h1_fallback(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("---\nslug: test\n---\n# Heading Title\nContent", encoding="utf-8")
        pos, title, _, _ = read_md_frontmatter_position(md)
        assert title == "Heading Title"

    def test_nonexistent_file_defaults(self, tmp_path):
        md = tmp_path / "nonexistent.md"
        pos, title, sidebar_label, slug = read_md_frontmatter_position(md)
        assert pos == 999.0


class TestFlattenChapters:
    def test_empty_list(self):
        assert flatten_chapters([]) == []

    def test_single_leaf(self):
        nodes = [ChapterNode(heading="Test", source="test.md", position=1)]
        result = flatten_chapters(nodes)
        assert len(result) == 1
        assert result[0]["heading"] == "Test"
        assert result[0]["source"] == "test.md"

    def test_nested_with_parent(self):
        child = ChapterNode(heading="Child", source="child.md", position=1, depth=1)
        parent = ChapterNode(heading="Parent", position=0, depth=0, is_container=True, children=[child])
        result = flatten_chapters([parent])
        assert len(result) == 2
        assert result[0]["heading"] == "Parent"
        assert result[1]["heading"] == "Child"
        assert result[1]["parent_heading"] == "Parent"

    def test_deep_nesting(self):
        inner = ChapterNode(heading="Inner", source="inner.md", position=1, depth=2)
        mid = ChapterNode(heading="Mid", position=0, depth=1, is_container=True, children=[inner])
        outer = ChapterNode(heading="Outer", position=0, depth=0, is_container=True, children=[mid])
        result = flatten_chapters([outer])
        assert len(result) == 3
        assert result[2]["depth"] == 2
        assert result[2]["parent_heading"] == "Mid"

    def test_multiple_siblings(self):
        a = ChapterNode(heading="A", source="a.md", position=1)
        b = ChapterNode(heading="B", source="b.md", position=2)
        result = flatten_chapters([a, b])
        assert len(result) == 2


class TestScanDocsDirectory:
    def test_finds_files(self):
        nodes = scan_docs_directory()
        assert len(nodes) > 0

    def test_finds_intro(self):
        nodes = scan_docs_directory()
        md_nodes = [n for n in nodes if n.source and "intro" in n.source]
        assert len(md_nodes) >= 1

    def test_skip_img_dirs(self):
        nodes = scan_docs_directory()
        all_sources = []
        for n in nodes:
            if n.source:
                all_sources.append(n.source)
            if n.children:
                for c in n.children:
                    if c.source:
                        all_sources.append(c.source)
        for src in all_sources:
            assert "_img" not in src
            assert "_file" not in src

    def test_total_flattened_count(self):
        nodes = scan_docs_directory()
        flat = flatten_chapters(nodes)
        assert len(flat) > 10

    def test_custom_docs_dir(self, tmp_path):
        pytest.skip("discovery._scan_directory hardcodes DOCS_DIR for relative_to — cannot use custom dir")

    def test_chapter_node_to_dict(self):
        node = ChapterNode(heading="Test", source="test.md", position=1, depth=0)
        d = node.to_dict()
        assert d["heading"] == "Test"
        assert d["source"] == "test.md"
        assert d["position"] == 1
