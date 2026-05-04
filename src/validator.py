# FILE: src/validator.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Проверка целостности GRACE .docx: XML-валидация, баланс закладок, Content_Types
#   SCOPE: validate_grace_docx
#   DEPENDS: M-GRACE
#   LINKS: M-VALIDATOR
#   ROLE: RUNTIME
#   MAP_MODE: EXPORTS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   validate_grace_docx - полная проверка GRACE .docx файла
# END_MODULE_MAP

import zipfile
from pathlib import Path

from lxml import etree


GRACE_PART_NAMES = [
    "grace-manifest.xml",
    "grace-instructions.xml",
    "grace-graph.xml",
    "grace-contracts.xml",
    "grace-verification.xml",
]


# START_BLOCK_VALIDATE_XML
def _validate_grace_xml(zf):
    """Проверить, что все grace-*.xml well-formed. Возвращает список ошибок."""
    errors = []
    for name in GRACE_PART_NAMES:
        path = f"word/{name}"
        try:
            content = zf.read(path)
            etree.fromstring(content)
        except KeyError:
            errors.append(f"MISSING: {path}")
        except etree.XMLSyntaxError as e:
            errors.append(f"INVALID XML: {path} — {e}")
    return errors
# END_BLOCK_VALIDATE_XML


# START_BLOCK_VALIDATE_BOOKMARKS
def _validate_bookmarks(zf):
    """Проверить парность GRACE-закладок. Возвращает (starts, ends, errors)."""
    doc_xml = zf.read("word/document.xml").decode("utf-8")
    import re
    starts = len(re.findall(r'<w:bookmarkStart\b', doc_xml))
    ends = len(re.findall(r'<w:bookmarkEnd\b', doc_xml))
    grace_count = doc_xml.count("GRACE_")
    errors = []
    if starts != ends:
        errors.append(f"BOOKMARK IMBALANCE: bookmarkStart={starts}, bookmarkEnd={ends}")
    if grace_count == 0:
        errors.append("NO GRACE BOOKMARKS FOUND")
    return starts, ends, grace_count, errors
# END_BLOCK_VALIDATE_BOOKMARKS


# START_BLOCK_VALIDATE_CONTENT_TYPES
def _validate_content_types(zf):
    """Проверить регистрацию GRACE-частей в Content_Types и rels."""
    errors = []
    ct = zf.read("[Content_Types].xml").decode("utf-8")
    for name in GRACE_PART_NAMES:
        if name not in ct:
            errors.append(f"CONTENT_TYPES MISSING: {name}")

    rels_path = "word/_rels/document.xml.rels"
    try:
        rels = zf.read(rels_path).decode("utf-8")
        for i in range(1, 6):
            rid = f"rIdGrace{i}"
            if rid not in rels:
                errors.append(f"RELS MISSING: {rid}")
    except KeyError:
        errors.append("RELS FILE MISSING")

    return errors
# END_BLOCK_VALIDATE_CONTENT_TYPES


# START_BLOCK_VALIDATE_GRACE_DOCX
def validate_grace_docx(docx_path):
    """Полная проверка GRACE .docx. Возвращает dict с результатами."""
    path = Path(docx_path)
    if not path.exists():
        return {"valid": False, "error": f"File not found: {path}"}

    result = {"valid": True, "file": str(path), "errors": [], "details": {}}

    with zipfile.ZipFile(str(path), "r") as zf:
        xml_errors = _validate_grace_xml(zf)
        result["details"]["xml_errors"] = xml_errors
        result["errors"].extend(xml_errors)

        starts, ends, grace_count, bm_errors = _validate_bookmarks(zf)
        result["details"]["bookmarks"] = {"starts": starts, "ends": ends, "grace_count": grace_count}
        result["errors"].extend(bm_errors)

        ct_errors = _validate_content_types(zf)
        result["details"]["content_types_errors"] = ct_errors
        result["errors"].extend(ct_errors)

    if result["errors"]:
        result["valid"] = False
    return result
# END_BLOCK_VALIDATE_GRACE_DOCX
