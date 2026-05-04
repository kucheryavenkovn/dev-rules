# FILE: src/renderer.py
# VERSION: 1.2.1
# START_MODULE_CONTRACT
#   PURPOSE: Рендеринг HTML-контента в элементы docx: параграфы, таблицы, списки, код, изображения
#   SCOPE: render_html_to_doc, render_paragraph, render_table, render_list, render_image
#   DEPENDS: M-CONFIG, M-TYPES
#   LINKS: M-RENDERER
#   ROLE: RUNTIME
#   MAP_MODE: EXPORTS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   render_html_to_doc - главная функция рендеринга HTML → docx
#   render_paragraph - рендеринг параграфа с inline-стилями
#   render_table - рендеринг HTML таблицы в Word таблицу
#   render_list - рендеринг списка с вложенностью (явная нумерация, перезапуск)
#   render_image - встраивание изображения из docs/ в docx
# END_MODULE_MAP

import logging
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

from src.types import ChapterInfo

from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.table import WD_TABLE_ALIGNMENT

logger = logging.getLogger(__name__)


# START_BLOCK_RENDER_HTML
def render_html_to_doc(doc, html_content, depth_offset=0, _recursion_depth=0, img_base_dir=None):
    """Рендерить HTML-контент в параграфы docx."""
    if _recursion_depth > 5:
        return
    logger.debug("[Renderer][render_html_to_doc][BLOCK_RENDER_HTML] depth_offset=%d recursion=%d len=%d", depth_offset, _recursion_depth, len(html_content))
    soup = BeautifulSoup(html_content, "html.parser")

    for element in soup.children:
        if isinstance(element, NavigableString):
            text = str(element).strip()
            if text:
                doc.add_paragraph(text)
            continue

        tag = element.name

        if tag in ("h1", "h2", "h3", "h4"):
            level = int(tag[1]) + depth_offset
            level = min(level, 4)
            text = element.get_text(strip=True)
            if text:
                doc.add_heading(text, level=level)

        elif tag == "p":
            render_paragraph(doc, element, img_base_dir=img_base_dir)

        elif tag == "pre":
            code_el = element.find("code")
            text = code_el.get_text() if code_el else element.get_text()
            for line in text.splitlines():
                p = doc.add_paragraph(line)
                p.style = doc.styles["Code"]
                pf = p.paragraph_format
                pf.space_before = Pt(0)
                pf.space_after = Pt(0)
                pf.left_indent = Cm(0.5)

        elif tag == "table":
            render_table(doc, element)

        elif tag in ("ul", "ol"):
            render_list(doc, element, ordered=(tag == "ol"))

        elif tag == "blockquote":
            text = element.get_text(strip=True)
            p = doc.add_paragraph(text)
            p.paragraph_format.left_indent = Cm(1.0)
            for run in p.runs:
                run.italic = True
                run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

        elif tag == "hr":
            pass

        elif tag in ("div", "section"):
            render_html_to_doc(doc, str(element), depth_offset, _recursion_depth + 1, img_base_dir=img_base_dir)

        elif tag == "img":
            src = element.get("src", "")
            render_image(doc, src, img_base_dir)

        elif tag in ("svg", "mermaid"):
            pass

        else:
            text = element.get_text(strip=True)
            if text:
                doc.add_paragraph(text)
# END_BLOCK_RENDER_HTML


# START_BLOCK_RENDER_PARAGRAPH
def render_paragraph(doc, element, img_base_dir=None):
    """Рендерить HTML параграф с inline-стилями."""
    p = doc.add_paragraph()
    for child in element.children:
        if isinstance(child, NavigableString):
            text = str(child)
            if text.strip():
                p.add_run(text)
        elif child.name in ("strong", "b"):
            r = p.add_run(child.get_text())
            r.bold = True
        elif child.name in ("em", "i"):
            r = p.add_run(child.get_text())
            r.italic = True
        elif child.name == "code":
            r = p.add_run(child.get_text())
            r.font.name = "Consolas"
            r.font.size = Pt(9)
        elif child.name == "a":
            text = child.get_text()
            if text.strip():
                r = p.add_run(text)
                r.font.color.rgb = RGBColor(0x05, 0x63, 0xC1)
                r.underline = True
        elif child.name == "br":
            pass
        elif child.name == "img":
            src = child.get("src", "")
            render_image(doc, src, img_base_dir)
        else:
            text = child.get_text()
            if text.strip():
                p.add_run(text)
    return p
# END_BLOCK_RENDER_PARAGRAPH


# START_BLOCK_RENDER_LIST
def render_list(doc, element, ordered=False, level=0):
    """Рендерить HTML список."""
    items = element.find_all("li", recursive=False)
    for idx, li in enumerate(items):
        text = li.get_text(strip=True)
        indent = Cm(0.5 * (level + 1))
        if ordered:
            p = doc.add_paragraph(f"{idx + 1}. {text}")
        else:
            p = doc.add_paragraph(text)
        p.paragraph_format.left_indent = indent
        p.style = doc.styles["Normal"]

        sublists = li.find_all(["ul", "ol"], recursive=False)
        for sub in sublists:
            render_list(doc, sub, ordered=(sub.name == "ol"), level=level + 1)
# END_BLOCK_RENDER_LIST


# START_BLOCK_RENDER_TABLE
def render_table(doc, element):
    """Рендерить HTML таблицу."""
    rows = element.find_all("tr")
    if not rows:
        logger.debug("[Renderer][render_table][BLOCK_RENDER_TABLE] skipped=no_rows")
        return

    first_row = rows[0]
    cols = first_row.find_all(["td", "th"])
    num_cols = len(cols)
    if num_cols == 0:
        logger.debug("[Renderer][render_table][BLOCK_RENDER_TABLE] skipped=no_cols")
        return

    table = doc.add_table(rows=min(len(rows), 100), cols=num_cols)
    table.style = "Light Grid Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    for i, row in enumerate(rows):
        cells = row.find_all(["td", "th"])
        for j, cell in enumerate(cells):
            if j < num_cols:
                text = cell.get_text(strip=True)
                table.rows[i].cells[j].text = text
                if row.find("th") or cell.name == "th":
                    for p in table.rows[i].cells[j].paragraphs:
                        for run in p.runs:
                            run.bold = True
                            run.font.size = Pt(10)
                else:
                    for p in table.rows[i].cells[j].paragraphs:
                        for run in p.runs:
                            run.font.size = Pt(10)

    logger.info("[Renderer][render_table][BLOCK_RENDER_TABLE] rows=%d cols=%d", len(rows), num_cols)
    doc.add_paragraph()
# END_BLOCK_RENDER_TABLE


# START_BLOCK_RENDER_IMAGE
def render_image(doc, src, img_base_dir=None):
    """Встроить изображение в docx или вставить плейсхолдер."""
    if not src:
        return

    image_path = None
    if img_base_dir is not None:
        candidate = Path(img_base_dir) / src
        if candidate.exists():
            image_path = candidate

    if image_path is not None:
        try:
            doc.add_picture(str(image_path), width=Inches(5.5))
            logger.info("[Renderer][render_image][BLOCK_RENDER_IMAGE] embedded=%s", src)
        except Exception as e:
            logger.warning("[Renderer][render_image][BLOCK_RENDER_IMAGE] failed=%s error=%s", src, e)
            doc.add_paragraph(f"[Image: {src}]")
    else:
        logger.warning("[Renderer][render_image][BLOCK_RENDER_IMAGE] not_found=%s", src)
        doc.add_paragraph(f"[Image: {src}]")
# END_BLOCK_RENDER_IMAGE

# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.2.1 — render_paragraph now handles <img> children inside <p> tags, passing img_base_dir through
# END_CHANGE_SUMMARY
