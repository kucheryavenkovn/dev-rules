# FILE: src/main.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Точка входа генератора Word-документа с GRACE-разметкой
#   SCOPE: main — сборка документа: титульная → оглавление → главы → GRACE инъекция → валидация
#   DEPENDS: M-CONFIG, M-RENDERER, M-STRUCTURE, M-GRACE, M-VALIDATOR, M-DISCOVERY, M-GRAPHSYNC
#   LINKS: M-DOCXBUILDER
#   ROLE: ENTRY_POINT
#   MAP_MODE: EXPORTS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   main - точка входа: синхронизация графа → генерация docx → GRACE инъекция → валидация
# END_MODULE_MAP

import sys
import io
import logging
from datetime import date

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from src.config import (
    setup_styles, classify_module_type, DOC_NAME, DOC_VERSION,
    OUTPUT_PATH, GRACE_VERSION, derive_module_id,
)
from src.parser import read_md, md_to_html
from src.structure import collect_chapters
from src.renderer import render_html_to_doc
from src.grace_injector import inject_grace_parts, inject_bookmark_start, inject_bookmark_end
from src.validator import validate_grace_docx
from src.graph_sync import sync_graph_from_fs

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    today_str = date.today().isoformat()

    print("=== Генерация Word-документа с GRACE-разметкой ===\n")

    # START_BLOCK_SYNC_GRAPH
    print("[1/6] Синхронизация knowledge-graph.xml с файловой системой...")
    flat = sync_graph_from_fs()
    print(f"       Обнаружено {len(flat)} глав в docs/")
    # END_BLOCK_SYNC_GRAPH

    # START_BLOCK_BUILD_DOC
    print("[2/6] Сборка документа Word...")
    doc = Document()
    setup_styles(doc)

    for _ in range(6):
        doc.add_paragraph()

    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title_p.add_run("СТАНДАРТЫ РАЗРАБОТКИ")
    r.font.size = Pt(28)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)

    subtitle_p = doc.add_paragraph()
    subtitle_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = subtitle_p.add_run("Гид по внутренним процессам и стандартам\nпроектной команды")
    r.font.size = Pt(16)
    r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    doc.add_paragraph()
    doc.add_paragraph()

    ver_p = doc.add_paragraph()
    ver_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = ver_p.add_run(f"Версия {DOC_VERSION}")
    r.font.size = Pt(12)
    r.font.color.rgb = RGBColor(0x88, 0x88, 0x88)

    date_p = doc.add_paragraph()
    date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = date_p.add_run(today_str)
    r.font.size = Pt(12)
    r.font.color.rgb = RGBColor(0x88, 0x88, 0x88)

    doc.add_paragraph()
    doc.add_paragraph()

    org_p = doc.add_paragraph()
    org_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = org_p.add_run("yellow-hammer / dev-rules")
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    doc.add_page_break()
    # END_BLOCK_BUILD_DOC

    # START_BLOCK_TOC
    print("[3/6] Построение оглавления...")
    chapters = collect_chapters(use_graph=True)
    if not chapters:
        print("       Fallback: chapters пустые, используем discovery напрямую")
        chapters = collect_chapters(use_graph=False)

    toc_heading = doc.add_heading("Оглавление", level=1)

    for ch in chapters:
        toc_p = doc.add_paragraph()
        toc_p.paragraph_format.left_indent = Cm(ch.get("depth", 0) * 0.75)
        r = toc_p.add_run(ch["heading"])
        if ch.get("depth", 0) == 0:
            r.bold = True
            r.font.size = Pt(12)
        else:
            r.font.size = Pt(11)

    doc.add_page_break()
    # END_BLOCK_TOC

    # START_BLOCK_CHAPTERS
    print(f"[4/6] Генерация {len(chapters)} глав...")
    para_counter = 0
    table_counter = 0
    h1_counter = 0
    h2_counter = 0
    bookmark_id = 100
    modules_info = []

    for ch in chapters:
        mid = ch.get("module_id") or derive_module_id(ch["heading"], {m["id"] for m in modules_info})
        depth = ch.get("depth", 0)
        heading_level = min(depth + 1, 4)

        heading_para = doc.add_heading(ch["heading"], level=heading_level)

        inject_bookmark_start(heading_para, bookmark_id, mid)

        ch["bookmark_start_id"] = bookmark_id
        ch["para_start"] = para_counter
        bookmark_id += 1
        para_counter += 1

        if heading_level == 1:
            h1_counter += 1
        elif heading_level == 2:
            h2_counter += 1

        mod_type = "NARRATIVE"
        mod_elements = []

        if ch.get("source"):
            title, md_text = read_md(ch["source"])
            if md_text:
                html = md_to_html(md_text)
                mod_type = classify_module_type(html)

                html_tables = html.lower().count("<table>")
                table_counter += html_tables
                for t_idx in range(html_tables):
                    mod_elements.append({
                        "type": "TABLE-DATA",
                        "para-index": str(para_counter + t_idx),
                        "columns": "0",
                        "rows": "0",
                    })

                render_html_to_doc(doc, html, depth_offset=depth)
                para_counter += len(html.split("<p>")) + len(html.split("<h")) + len(html.split("<li>"))

        else:
            mod_type = "NAVIGATION"

        ch["type"] = mod_type
        ch["para_end"] = para_counter - 1

        inject_bookmark_end(doc, ch["bookmark_start_id"])

        modules_info.append({
            "id": mid,
            "heading": ch["heading"],
            "type": mod_type,
            "para_start": ch["para_start"],
            "para_end": ch["para_end"],
            "elements": mod_elements,
            "subsections": [],
            "parent": ch.get("parent_heading"),
            "parent_heading": ch.get("parent_heading"),
        })
    # END_BLOCK_CHAPTERS

    # START_BLOCK_SAVE_AND_INJECT
    print("[5/6] Сохранение и GRACE-инъекция...")
    doc.save(str(OUTPUT_PATH))

    grace_output = OUTPUT_PATH.parent / f"GRACE_{OUTPUT_PATH.name}"
    inject_grace_parts(
        base_docx_path=OUTPUT_PATH,
        grace_docx_path=grace_output,
        modules_info=modules_info,
        total_paras=para_counter,
        total_tables=table_counter,
        total_h1=h1_counter,
        total_h2=h2_counter,
        today_str=today_str,
    )
    # END_BLOCK_SAVE_AND_INJECT

    # START_BLOCK_VALIDATE
    print("[6/6] Валидация...")
    result = validate_grace_docx(grace_output)
    status = "OK" if result["valid"] else "FAILED"
    print(f"       Валидация: {status}")
    if not result["valid"]:
        for err in result["errors"]:
            print(f"       ERROR: {err}")
    # END_BLOCK_VALIDATE

    # START_BLOCK_REPORT
    print(f"""
=============================================
GRACE-DOCX Bootstrap Complete  [v3]
=============================================
Document:        {DOC_NAME}
Version:         {DOC_VERSION}
Modules:         {len(modules_info)}
XML parts:       5 injected
Bookmarks:       {len(modules_info)} pairs
Graph synced:    docs/knowledge-graph.xml → grace-graph.xml
---------------------------------------------""")

    for mod in modules_info:
        print(f"  {mod['id']:12s}  {mod['type']:12s}  {mod['heading']}")

    print(f"""---------------------------------------------
Output:
  Base:    {OUTPUT_PATH}
  GRACE:   {grace_output}
  Status:  {status}
=============================================""")
    # END_BLOCK_REPORT


if __name__ == "__main__":
    main()
