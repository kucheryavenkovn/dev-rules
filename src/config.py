# FILE: src/config.py
# VERSION: 1.0.1
# START_MODULE_CONTRACT
#   PURPOSE: Конфигурация генератора: пути, версия документа, стили Word, маппинг заголовков → Module ID
#   SCOPE: derive_module_id, classify_module_type, setup_styles, константы путей
#   DEPENDS: none
#   LINKS: M-CONFIG
#   ROLE: RUNTIME
#   MAP_MODE: EXPORTS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   DOCS_DIR - путь к каталогу с Markdown-файлами
#   OUTPUT_PATH - путь к выходному .docx файлу
#   DOC_NAME - название документа
#   DOC_VERSION - версия документа
#   GRACE_VERSION - версия GRACE
#   derive_module_id - генерация уникального Module ID из заголовка
#   classify_module_type - классификация типа модуля по HTML
#   setup_styles - настройка стилей документа Word
# END_MODULE_MAP

import logging
import re
from datetime import date
from pathlib import Path

from docx.shared import Pt, Cm, RGBColor
from docx.enum.style import WD_STYLE_TYPE

logger = logging.getLogger(__name__)

# START_BLOCK_CONSTANTS
DOCS_DIR = Path(r"D:\git\dev-rules\docs")
OUTPUT_PATH = Path(r"D:\git\dev-rules\Стандарты_разработки.docx")
DOC_NAME = "Стандарты разработки"
DOC_VERSION = "1.0"
GRACE_VERSION = "3.0.0"
TODAY = date.today().isoformat()
# END_BLOCK_CONSTANTS

# START_BLOCK_MODULE_ID_MAP
_MODULE_ID_SPECIAL = {
    "Введение": "M-INTRO",
    "Начало разработки": "M-BEGIN",
    "Оформление кода": "M-LAYOUT",
    "Запросы": "M-QUERY",
    "Управляемые формы": "M-FORMS",
    "Блокировка форм": "M-BLOCK",
    "Ввод на основании": "M-INPUT",
    "Расширения": "M-EXT",
    "Печатные формы": "M-PRINT",
    "Префикс и комментарии": "M-PREFIX",
    "Принципы эффективной разработки": "M-PRINC",
    "Метаданные": "M-META",
    "Система управления версиями": "M-VC",
    "Среды разработки": "M-IDE",
    "DevOps": "M-DEVOPS",
    "Интеграции": "M-INTEG",
    "Руководства пользователя": "M-MANUAL",
    "Глоссарий терминов": "M-GLOSS",
    "KISS — Делай проще": "M-KISS",
    "DRY — Не повторяйся": "M-DRY",
    "YAGNI — Вам это не понадобится": "M-YAGNI",
    "SOLID": "M-SOLID",
    "Архитектура 1С-решений": "M-ARCH",
    "Общие модули": "M-COMMON",
    "Справочники": "M-CATALOG",
    "Документы": "M-DOCS",
    "Регистры накопления": "M-ACCREG",
    "Регистры сведений": "M-INFREG",
    "Подсистемы": "M-SUBSYS",
    "Отчеты": "M-REPORTS",
    "Роли": "M-ROLES",
    "Подписки на события": "M-EVTSUB",
    "Регламентные задания": "M-SCHED",
    "Обзор": "M-OVERVIEW",
    "Хранилище 1С": "M-1CSTOR",
    "Работа с Git": "M-GIT",
    "Основные команды Git": "M-GITCMD",
    "Настройка SSH ключей": "M-SSH",
    "Git Flow": "M-GITFLOW",
    "Настройка исключений Git": "M-GITIGN",
    "Настройка атрибутов Git": "M-GITATTR",
    "Git LFS": "M-LFS",
    "Подмодули Git": "M-SUBMOD",
    "Phoenix BSL": "M-PHOENIX",
    "Visual Studio Code": "M-VSCODE",
    "1С:EDT": "M-EDT",
    "Code-review": "M-CR",
    "Конвейеры CI/CD": "M-PIPE",
    "Профиль Jenkins": "M-JENKINS",
    "Профиль GitLab CI": "M-GITLAB",
    "Тестирование": "M-TEST",
    "Стратегия тестирования": "M-TESTSTR",
    "Инициализация тестовой ИБ": "M-TESTDATA",
    "Чек-лист ЗУП": "M-HRMCHK",
    "Доставка и развертывание": "M-DELIVER",
    "SonarQube": "M-SONAR",
    "Брокеры сообщений": "M-MSG",
    "RabbitMQ": "M-RMQ",
    "Основные концепции": "M-RMQCON",
    "Регламент именования": "M-RMQNAM",
    "БИТ.Адаптер": "M-BITADPT",
    "Apache Kafka": "M-KAFKA",
    "Окружения": "M-ENV",
    "Пользователи": "M-USERS",
    "Обновление конфигураций": "M-UPDATE",
    "Жизненный цикл задачи": "M-TASK",
}
# END_BLOCK_MODULE_ID_MAP


# START_BLOCK_DERIVE_ID
def derive_module_id(heading, existing_ids):
    """Генерация Module ID из заголовка. Возвращает уникальный латинский ID."""
    mid = _MODULE_ID_SPECIAL.get(heading)
    if mid:
        if mid not in existing_ids:
            logger.info("[Config][derive_module_id][BLOCK_DERIVE_ID] resolved=%s heading='%s' source=special", mid, heading)
            return mid
        base = mid
        counter = 2
        while f"{base}-{counter}" in existing_ids:
            counter += 1
        resolved = f"{base}-{counter}"
        logger.info("[Config][derive_module_id][BLOCK_DERIVE_ID] resolved=%s heading='%s' source=special-dup counter=%d", resolved, heading, counter)
        return resolved
    clean = re.sub(r"[^A-Za-z0-9]", "", heading).upper()
    if len(clean) >= 3:
        candidate = "M-" + clean[:5]
    else:
        candidate = "M-SEC" + str(len(existing_ids) + 100)
    while candidate in existing_ids:
        candidate = candidate + str(len(existing_ids))
    logger.info("[Config][derive_module_id][BLOCK_DERIVE_ID] resolved=%s heading='%s' source=generated", candidate, heading)
    return candidate
# END_BLOCK_DERIVE_ID


# START_BLOCK_CLASSIFY_TYPE
def classify_module_type(html_content):
    """Определить тип модуля GRACE по HTML-содержимому."""
    has_tables = "<table>" in html_content.lower()
    has_code = "<code>" in html_content.lower() or "<pre>" in html_content.lower()
    has_prose = "<p>" in html_content.lower()
    if has_tables and has_code and has_prose:
        result = "MIXED"
    elif has_tables and has_code:
        result = "MIXED"
    elif has_tables:
        result = "DATA"
    elif has_code or has_prose:
        result = "NARRATIVE"
    else:
        result = "NARRATIVE"
    logger.debug("[Config][classify_module_type][BLOCK_CLASSIFY_TYPE] type=%s tables=%s code=%s prose=%s", result, has_tables, has_code, has_prose)
    return result
# END_BLOCK_CLASSIFY_TYPE


# START_BLOCK_SETUP_STYLES
def setup_styles(doc):
    """Настроить стили документа Word."""
    logger.info("[Config][setup_styles][BLOCK_SETUP_STYLES] configuring styles")
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.line_spacing = 1.15

    for i in range(1, 5):
        sname = f"Heading {i}"
        if sname in doc.styles:
            s = doc.styles[sname]
            s.font.name = "Calibri"
            if i == 1:
                s.font.size = Pt(22)
                s.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
                s.font.bold = True
            elif i == 2:
                s.font.size = Pt(16)
                s.font.color.rgb = RGBColor(0x2C, 0x5F, 0x2D)
                s.font.bold = True
            elif i == 3:
                s.font.size = Pt(13)
                s.font.color.rgb = RGBColor(0x4A, 0x4A, 0x4A)
                s.font.bold = True
            elif i == 4:
                s.font.size = Pt(11)
                s.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
                s.font.bold = True
            s.paragraph_format.space_before = Pt(12)
            s.paragraph_format.space_after = Pt(6)

    if "Code" not in [s.name for s in doc.styles]:
        cs = doc.styles.add_style("Code", WD_STYLE_TYPE.PARAGRAPH)
        cs.font.name = "Courier New"
        cs.font.size = Pt(8)
        cs.font.color.rgb = RGBColor(0x2D, 0x2D, 0x2D)
        cs.paragraph_format.space_before = Pt(2)
        cs.paragraph_format.space_after = Pt(2)
        cs.paragraph_format.left_indent = Cm(0.5)
# END_BLOCK_SETUP_STYLES


# START_BLOCK_BOOKMARK_NAME
def make_bookmark_name(module_id):
    """Конструировать имя GRACE-закладки из module_id."""
    return f"GRACE_{module_id}"
# END_BLOCK_BOOKMARK_NAME
