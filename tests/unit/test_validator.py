# FILE: tests/unit/test_validator.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Юнит-тесты модуля M-VALIDATOR (src/validator.py)
#   SCOPE: validate_grace_docx, внутренние функции валидации
#   DEPENDS: M-VALIDATOR
#   LINKS: V-M-VALIDATOR
#   ROLE: TEST
#   MAP_MODE: LOCALS
# END_MODULE_CONTRACT

import zipfile
import pytest
from pathlib import Path

from src.validator import validate_grace_docx, GRACE_PART_NAMES


GRACE_DOCX = Path(r"D:\git\dev-rules\GRACE_Стандарты_разработки.docx")


@pytest.mark.skipif(not GRACE_DOCX.exists(), reason="GRACE .docx not generated yet")
class TestValidateGraceDocx:
    def test_valid_grace_docx(self):
        result = validate_grace_docx(GRACE_DOCX)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_bookmarks_balanced(self):
        result = validate_grace_docx(GRACE_DOCX)
        bm = result["details"]["bookmarks"]
        assert bm["starts"] == bm["ends"]
        assert bm["grace_count"] > 0

    def test_all_grace_parts_present(self):
        with zipfile.ZipFile(str(GRACE_DOCX), "r") as zf:
            names = zf.namelist()
        for name in GRACE_PART_NAMES:
            assert f"word/{name}" in names

    def test_nonexistent_file(self):
        result = validate_grace_docx(Path("/nonexistent/file.docx"))
        assert result["valid"] is False
        assert "not found" in result["error"].lower()


class TestValidatorUnit:
    def test_grace_part_names_count(self):
        assert len(GRACE_PART_NAMES) == 5
