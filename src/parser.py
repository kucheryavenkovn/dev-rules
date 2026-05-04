# FILE: src/parser.py
# VERSION: 1.0.0
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
#   md_to_html - конвертировать Markdown → HTML
# END_MODULE_MAP

import markdown

from src.config import DOCS_DIR


# START_BLOCK_PARSE_FRONTMATTER
def strip_frontmatter(text):
    """Удалить YAML frontmatter из markdown."""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
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
                    return line.split(":", 1)[1].strip().strip('"').strip("'")
    return None
# END_BLOCK_PARSE_FRONTMATTER


# START_BLOCK_READ_MD
def read_md(rel_path):
    """Прочитать markdown файл и вернуть (title, clean_text)."""
    fpath = DOCS_DIR / rel_path
    if not fpath.exists():
        return None, None
    text = fpath.read_text(encoding="utf-8")
    title = get_frontmatter_title(text)
    clean = strip_frontmatter(text)
    if title is None:
        for line in clean.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
    return title, clean
# END_BLOCK_READ_MD


# START_BLOCK_MD_TO_HTML
def md_to_html(md_text):
    """Конвертировать Markdown → HTML через библиотеку markdown."""
    return markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "toc", "codehilite"],
        extension_defaults={"codehilite": {"guess_lang": False}},
    )
# END_BLOCK_MD_TO_HTML
