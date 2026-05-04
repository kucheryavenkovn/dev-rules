# FILE: src/discovery.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Динамическое обнаружение структуры документации из файловой системы Docusaurus
#   SCOPE: scan_docs_directory, read_category_json, read_md_frontmatter_position
#   DEPENDS: M-CONFIG (DOCS_DIR)
#   LINKS: M-DISCOVERY
#   ROLE: RUNTIME
#   MAP_MODE: EXPORTS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   scan_docs_directory - сканирует docs/ и строит иерархию глав с позициями
#   read_category_json - читает _category_.json из каталога
#   read_md_frontmatter_position - извлекает sidebar_position и title из .md
#   ChapterNode - dataclass узла главы (heading, source, position, children)
# END_MODULE_MAP

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.config import DOCS_DIR


@dataclass
class ChapterNode:
    heading: str
    source: Optional[str] = None
    position: float = 0
    children: list = field(default_factory=list)
    depth: int = 0
    rel_path: str = ""
    is_container: bool = False

    def to_dict(self):
        result = {
            "heading": self.heading,
            "position": self.position,
            "depth": self.depth,
            "rel_path": self.rel_path,
            "is_container": self.is_container,
        }
        if self.source:
            result["source"] = self.source
        if self.children:
            result["children"] = [c.to_dict() for c in self.children]
        return result


# START_BLOCK_READ_CATEGORY
def read_category_json(dir_path):
    """Прочитать _category_.json из каталога. Возвращает (label, position) или (None, 999)."""
    cat_file = dir_path / "_category_.json"
    if cat_file.exists():
        try:
            data = json.loads(cat_file.read_text(encoding="utf-8"))
            label = data.get("label", dir_path.name)
            position = data.get("position", 999)
            return label, position
        except (json.JSONDecodeError, KeyError):
            pass
    return dir_path.name, 999
# END_BLOCK_READ_CATEGORY


# START_BLOCK_READ_FM_POSITION
def read_md_frontmatter_position(md_path):
    """Извлечь sidebar_position и title из frontmatter .md файла."""
    position = 999.0
    title = None
    sidebar_label = None
    slug = None
    try:
        text = md_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return position, title, sidebar_label, slug

    if not text.startswith("---"):
        return position, title, sidebar_label, slug

    parts = text.split("---", 2)
    if len(parts) < 3:
        return position, title, sidebar_label, slug

    fm = parts[1]
    for line in fm.splitlines():
        stripped = line.strip()
        if stripped.startswith("sidebar_position:"):
            try:
                position = float(stripped.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif stripped.startswith("title:"):
            title = stripped.split(":", 1)[1].strip().strip('"').strip("'")
        elif stripped.startswith("sidebar_label:"):
            sidebar_label = stripped.split(":", 1)[1].strip().strip('"').strip("'")
        elif stripped.startswith("slug:"):
            slug = stripped.split(":", 1)[1].strip().strip('"').strip("'")

    if title is None:
        clean = parts[2].strip()
        for line in clean.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break

    return position, title, sidebar_label, slug
# END_BLOCK_READ_FM_POSITION


_SKIP_DIRS = {"_file", "_img", "img", "file"}
_SKIP_FILES = {"_category_.json"}
_MD_EXTENSIONS = {".md", ".mdx"}


# START_BLOCK_SCAN_DIR
def _scan_directory(dir_path, depth=0):
    """Рекурсивно сканировать каталог и вернуть список ChapterNode."""
    nodes = []

    md_files = []
    subdirs = []

    try:
        entries = sorted(dir_path.iterdir())
    except OSError:
        return nodes

    for entry in entries:
        name = entry.name
        if name.startswith(".") or name.startswith("_"):
            if name in _SKIP_DIRS or name in _SKIP_FILES:
                continue
            if name.startswith("_"):
                continue
        if entry.is_dir() and name not in _SKIP_DIRS:
            subdirs.append(entry)
        elif entry.is_file() and entry.suffix in _MD_EXTENSIONS and name not in _SKIP_FILES:
            md_files.append(entry)

    for md_path in md_files:
        position, title, sidebar_label, slug = read_md_frontmatter_position(md_path)
        display_title = sidebar_label or title or md_path.stem
        rel = md_path.relative_to(DOCS_DIR)
        node = ChapterNode(
            heading=display_title,
            source=str(rel).replace("\\", "/"),
            position=position,
            depth=depth,
            rel_path=str(rel).replace("\\", "/"),
        )
        nodes.append(node)

    for subdir in subdirs:
        cat_label, cat_position = read_category_json(subdir)
        rel = subdir.relative_to(DOCS_DIR)

        readme_md = subdir / "README.md"
        source = None
        if readme_md.exists():
            source = str(readme_md.relative_to(DOCS_DIR)).replace("\\", "/")

        children = _scan_directory(subdir, depth + 1)

        container = ChapterNode(
            heading=cat_label,
            source=source,
            position=cat_position,
            depth=depth,
            rel_path=str(rel).replace("\\", "/") + "/",
            is_container=True,
            children=children,
        )
        nodes.append(container)

    nodes.sort(key=lambda n: n.position)
    return nodes
# END_BLOCK_SCAN_DIR


# START_BLOCK_SCAN_DOCS
def scan_docs_directory(docs_dir=None):
    """Сканировать docs/ и построить полную иерархию глав.

    Возвращает список ChapterNode, отсортированный по sidebar_position.
    """
    root = Path(docs_dir) if docs_dir else DOCS_DIR
    return _scan_directory(root, depth=0)
# END_BLOCK_SCAN_DOCS


# START_BLOCK_FLATTEN
def flatten_chapters(nodes, parent_heading=None):
    """Развернуть дерево ChapterNode в плоский список для генерации."""
    result = []
    for node in nodes:
        entry = {
            "heading": node.heading,
            "source": node.source,
            "depth": node.depth,
            "position": node.position,
            "parent_heading": parent_heading,
            "is_container": node.is_container,
            "rel_path": node.rel_path,
        }
        result.append(entry)
        if node.children:
            result.extend(flatten_chapters(node.children, parent_heading=node.heading))
    return result
# END_BLOCK_FLATTEN
