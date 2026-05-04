# FILE: src/graph_sync.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Синхронизация knowledge-graph.xml с файловой системой и обратно
#   SCOPE: sync_graph_from_fs, read_graph_modules, update_graph_xml, build_grace_graph_xml
#   DEPENDS: M-DISCOVERY, M-CONFIG, M-STRUCTURE
#   LINKS: M-GRAPHSYNC
#   ROLE: RUNTIME
#   MAP_MODE: EXPORTS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   sync_graph_from_fs - обновить knowledge-graph.xml из текущего состояния docs/
#   read_graph_modules - прочитать модули из knowledge-graph.xml
#   build_grace_graph_xml - построить grace-graph.xml для .docx из knowledge-graph.xml
#   chapters_from_graph - построить плоский список глав из knowledge-graph.xml
# END_MODULE_MAP

import logging
from datetime import date
from pathlib import Path

from lxml import etree

from src.config import DOCS_DIR, DOC_NAME, GRACE_VERSION, derive_module_id
from src.discovery import scan_docs_directory, flatten_chapters

logger = logging.getLogger(__name__)

GRAPH_PATH = DOCS_DIR.parent / "docs" / "knowledge-graph.xml"


# START_BLOCK_READ_GRAPH
def read_graph_modules(graph_path=None):
    """Прочитать модули из knowledge-graph.xml. Возвращает list[dict]."""
    path = Path(graph_path) if graph_path else GRAPH_PATH
    if not path.exists():
        return []

    modules = []
    try:
        tree = etree.parse(str(path))
        root = tree.getroot()
    except etree.XMLSyntaxError:
        return []

    for project in root.iterchildren():
        for mod_el in project.iterchildren():
            tag = mod_el.tag
            if not tag.startswith("M-"):
                continue
            mod = {
                "id": tag,
                "name": mod_el.get("NAME", ""),
                "type": mod_el.get("TYPE", ""),
                "status": mod_el.get("STATUS", ""),
            }
            purpose_el = mod_el.find("purpose")
            if purpose_el is not None:
                mod["purpose"] = purpose_el.text or ""
            path_el = mod_el.find("path")
            if path_el is not None:
                mod["path"] = path_el.text or ""
            depends_el = mod_el.find("depends")
            if depends_el is not None:
                mod["depends"] = depends_el.text or "none"
            modules.append(mod)
    return modules
# END_BLOCK_READ_GRAPH


# START_BLOCK_SYNC_FS_TO_GRAPH
def sync_graph_from_fs(graph_path=None):
    """Обновить knowledge-graph.xml из текущего состояния docs/.

    Считает _category_.json и frontmatter → обновляет модули-главы в графе.
    """
    path = Path(graph_path) if graph_path else GRAPH_PATH
    nodes = scan_docs_directory()
    flat = flatten_chapters(nodes)

    existing_ids = set()
    for mod in read_graph_modules(path):
        existing_ids.add(mod["id"])

    if path.exists():
        tree = etree.parse(str(path))
        root = tree.getroot()
    else:
        root = etree.Element("KnowledgeGraph")
        project = etree.SubElement(root, "Project")
        project.set("NAME", DOC_NAME)
        project.set("VERSION", "0.3.0")
        etree.SubElement(project, "keywords").text = "1C, BSL, Word, docx, GRACE, markdown, documentation"
        etree.SubElement(project, "annotation").text = "Генератор Word-документа стандартов разработки с GRACE-DOCX v3"

    project_el = root.find("Project")
    if project_el is None:
        project_el = root.find(".//*")

    doc_chapters_tag = "DocChapters"
    chapters_el = project_el.find(doc_chapters_tag)
    if chapters_el is None:
        chapters_el = etree.SubElement(project_el, doc_chapters_tag)

    for ch in chapters_el:
        pass

    chapters_el.clear()

    for ch in flat:
        mid = derive_module_id(ch["heading"], existing_ids)
        existing_ids.add(mid)
        mod_type = "NAVIGATION" if ch.get("is_container") else "NARRATIVE"
        mod_el = etree.SubElement(chapters_el, mid)
        mod_el.set("NAME", ch["heading"])
        mod_el.set("TYPE", mod_type)
        mod_el.set("STATUS", "auto-discovered")
        etree.SubElement(mod_el, "source").text = ch.get("source") or ""
        etree.SubElement(mod_el, "position").text = str(ch.get("position", 0))
        etree.SubElement(mod_el, "depth").text = str(ch.get("depth", 0))
        etree.SubElement(mod_el, "rel-path").text = ch.get("rel_path", "")
        parent = ch.get("parent_heading")
        if parent:
            etree.SubElement(mod_el, "parent").text = parent

    tree = etree.ElementTree(root)
    tree.write(str(path), encoding="UTF-8", xml_declaration=True, pretty_print=True)

    logger.info(f"[GraphSync][sync_graph_from_fs][BLOCK_SYNC_FS_TO_GRAPH] "
                f"synced {len(flat)} chapters to {path}")
    return flat
# END_BLOCK_SYNC_FS_TO_GRAPH


# START_BLOCK_CHAPTERS_FROM_GRAPH
def chapters_from_graph(graph_path=None):
    """Прочитать плоский список глав из секции DocChapters knowledge-graph.xml.

    Если секция DocChapters пуста или отсутствует — fallback на discovery.
    """
    path = Path(graph_path) if graph_path else GRAPH_PATH
    if not path.exists():
        return []

    try:
        tree = etree.parse(str(path))
        root = tree.getroot()
    except etree.XMLSyntaxError:
        return []

    project_el = root.find(".//Project")
    if project_el is None:
        return []

    chapters_el = project_el.find("DocChapters")
    if chapters_el is None:
        return []

    chapters = []
    for mod_el in chapters_el:
        tag = mod_el.tag
        if not tag.startswith("M-"):
            continue
        source_el = mod_el.find("source")
        pos_el = mod_el.find("position")
        depth_el = mod_el.find("depth")
        parent_el = mod_el.find("parent")
        rel_path_el = mod_el.find("rel-path")

        source = source_el.text if source_el is not None and source_el.text else None
        ch = {
            "heading": mod_el.get("NAME", ""),
            "source": source,
            "depth": int(depth_el.text) if depth_el is not None else 0,
            "position": float(pos_el.text) if pos_el is not None else 0,
            "is_container": mod_el.get("TYPE") == "NAVIGATION",
            "rel_path": rel_path_el.text if rel_path_el is not None else "",
            "module_id": tag,
            "parent_heading": parent_el.text if parent_el is not None else None,
        }
        chapters.append(ch)

    if not chapters:
        nodes = scan_docs_directory()
        flat = flatten_chapters(nodes)
        used_ids = set()
        for ch in flat:
            mid = derive_module_id(ch["heading"], used_ids)
            used_ids.add(mid)
            ch["module_id"] = mid
        chapters = flat

    return chapters
# END_BLOCK_CHAPTERS_FROM_GRAPH


# START_BLOCK_BUILD_GRACE_GRAPH
def build_grace_graph_xml(modules_info, total_paras, total_tables, total_h1, total_h2):
    """Построить grace-graph.xml для внедрения в .docx из modules_info."""
    modules_xml = ""
    for mod in modules_info:
        elements_xml = ""
        for el in mod.get("elements", []):
            attrs = " ".join(f'{k}="{v}"' for k, v in el.items())
            elements_xml += f'\n        <element {attrs}/>'
        if elements_xml:
            elements_xml = f"\n      <ELEMENTS>{elements_xml}\n      </ELEMENTS>"

        subs_xml = ""
        for sub in mod.get("subsections", []):
            subs_xml += f'\n        <sub id="{sub["id"]}">'
            subs_xml += f"\n          <heading>{sub['heading']}</heading>"
            subs_xml += f"\n          <para-start>{sub['para_start']}</para-start>"
            subs_xml += f"\n          <para-end>{sub['para_end']}</para-end>"
            subs_xml += "\n        </sub>"
        if subs_xml:
            subs_xml = f"\n      <SubSections>{subs_xml}\n      </SubSections>"

        mod_id = mod["id"]
        modules_xml += f'''
    <{mod_id}>
      <n>{mod["heading"]}</n>
      <TYPE>{mod["type"]}</TYPE>
      <BOOKMARK>GRACE_{mod_id}</BOOKMARK>
      <PARA-START>{mod["para_start"]}</PARA-START>
      <PARA-END>{mod["para_end"]}</PARA-END>{subs_xml}{elements_xml}
    </{mod_id}>'''

    cross_xml = ""
    for mod in modules_info:
        if mod.get("parent"):
            cross_xml += f'''
    <link>
      <from>{mod["id"]}</from>
      <to>{mod["parent"]}</to>
      <relation>contains: {mod["heading"]} → {mod.get("parent_heading", "")}</relation>
    </link>'''

    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<GraceGraph VERSION="{GRACE_VERSION}">
  <DocumentMeta>
    <total-paragraphs>{total_paras}</total-paragraphs>
    <total-tables>{total_tables}</total-tables>
    <total-h1>{total_h1}</total-h1>
    <total-h2>{total_h2}</total-h2>
    <source-graph>docs/knowledge-graph.xml</source-graph>
  </DocumentMeta>
  <Modules>{modules_xml}
  </Modules>
  <CrossLinks>{cross_xml}
  </CrossLinks>
</GraceGraph>'''
# END_BLOCK_BUILD_GRACE_GRAPH
