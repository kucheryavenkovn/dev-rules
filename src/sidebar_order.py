# FILE: src/sidebar_order.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Построение авторитетного порядка глав, идентичного Docusaurus sidebar auto-generation
#   SCOPE: build_chapter_order
#   DEPENDS: M-CONFIG, M-DISCOVERY, M-TYPES
#   LINKS: M-SIDEBAR
#   ROLE: RUNTIME
#   MAP_MODE: EXPORTS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   build_chapter_order - построить упорядоченный список глав через sidebar_position
# END_MODULE_MAP

import logging

from src.config import derive_module_id
from src.discovery import scan_docs_directory, flatten_chapters
from src.graph_sync import chapters_from_graph
from src.types import ChapterInfo

logger = logging.getLogger(__name__)


# START_BLOCK_BUILD_SIDEBAR_ORDER
def build_chapter_order(use_graph=True):
    if use_graph:
        graph_chapters = chapters_from_graph()
        if graph_chapters:
            result = [ChapterInfo.from_dict(ch) for ch in graph_chapters]
            logger.info(
                "[SidebarOrder][build_chapter_order][BUILD_SIDEBAR_ORDER] source=graph count=%d",
                len(result),
            )
            return result

    nodes = scan_docs_directory()
    flat = flatten_chapters(nodes)

    existing_ids = set()
    chapters = []
    for ch in flat:
        mid = derive_module_id(ch["heading"], existing_ids)
        existing_ids.add(mid)
        ch["module_id"] = mid
        chapters.append(ChapterInfo.from_dict(ch))

    logger.info(
        "[SidebarOrder][build_chapter_order][BUILD_SIDEBAR_ORDER] source=discovery count=%d",
        len(chapters),
    )
    return chapters
# END_BLOCK_BUILD_SIDEBAR_ORDER
