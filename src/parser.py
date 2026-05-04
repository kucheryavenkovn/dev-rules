# FILE: src/parser.py
# VERSION: 1.1.0
# START_MODULE_CONTRACT
#   PURPOSE: Чтение Markdown-файлов из docs/ и конвертация в HTML
#   SCOPE: read_md, strip_frontmatter, get_frontmatter_title, md_to_html
#   DEPENDS: M-CONFIG (DOCS_DIR)
#   LINKS: M-PARSER
#   ROLE: RUNTIME
#   MAP_MODE: EXPORTS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   read_md - прочитать .md файл, вернуть (title, clean_text)
#   strip_frontmatter - удалить YAML frontmatter
#   get_frontmatter_title - извлечь заголовок из frontmatter
#   md_to_html - конвертировать Markdown → HTML (с dedent fenced code)
#   _dedent_fenced_code - убрать отступы перед ``` для корректного парсинга
# END_MODULE_MAP

import logging
import re

import markdown

from src.config import DOCS_DIR

logger = logging.getLogger(__name__)


# START_BLOCK_PARSE_FRONTMATTER
def strip_frontmatter(text):
    """Удалить YAML frontmatter из markdown."""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            logger.debug("[Parser][strip_frontmatter][BLOCK_PARSE_FRONTMATTER] stripped frontmatter len=%d", len(parts[1]))
            return parts[2].strip()
    return text


def get_frontmatter_title(text):
    """Извлечь заголовок из frontmatter (title field)."""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm = parts[1]
            for line in fm.splitlines():
                if line.strip().startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip('"').strip("'")
                    logger.debug("[Parser][get_frontmatter_title][BLOCK_PARSE_FRONTMATTER] title='%s'", title)
                    return title
    return None
# END_BLOCK_PARSE_FRONTMATTER


# START_BLOCK_READ_MD
def read_md(rel_path):
    """Прочитать markdown файл и вернуть (title, clean_text)."""
    fpath = DOCS_DIR / rel_path
    if not fpath.exists():
        logger.warning("[Parser][read_md][BLOCK_READ_MD] file not found: %s", rel_path)
        return None, None
    text = fpath.read_text(encoding="utf-8")
    title = get_frontmatter_title(text)
    clean = strip_frontmatter(text)
    if title is None:
        for line in clean.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
    logger.info("[Parser][read_md][BLOCK_READ_MD] path=%s title='%s' len=%d", rel_path, title, len(clean))
    return title, clean
# END_BLOCK_READ_MD


# START_BLOCK_MD_TO_HTML
def _dedent_fenced_code(md_text):
    """Удалить отступы перед ``` линиями, чтобы markdown распознал fenced code blocks."""
    lines = md_text.split("\n")
    result = []
    in_fence = False
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            result.append(stripped)
        elif in_fence:
            result.append(stripped)
        else:
            result.append(line)
    return "\n".join(result)


def md_to_html(md_text):
    """Конвертировать Markdown → HTML через библиотеку markdown."""
    dedented = _dedent_fenced_code(md_text)
    html = markdown.markdown(
        dedented,
        extensions=["tables", "fenced_code", "toc"],
    )
    logger.debug("[Parser][md_to_html][BLOCK_MD_TO_HTML] output_len=%d", len(html))
    return html
# END_BLOCK_MD_TO_HTML
