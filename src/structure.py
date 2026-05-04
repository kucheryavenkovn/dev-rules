# FILE: src/structure.py
# VERSION: 1.0.1
# START_MODULE_CONTRACT
#   PURPOSE: Определение иерархии глав через динамическое обнаружение или knowledge-graph.xml
#   SCOPE: collect_chapters, chapters_from_discovery, chapters_from_graph
#   DEPENDS: M-DISCOVERY, M-GRAPHSYNC
#   LINKS: M-STRUCTURE
#   ROLE: RUNTIME
#   MAP_MODE: EXPORTS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   collect_chapters - получить плоский список глав (из графа → fallback discovery)
# END_MODULE_MAP

import logging

from src.discovery import scan_docs_directory, flatten_chapters
from src.graph_sync import chapters_from_graph
from src.config import derive_module_id

logger = logging.getLogger(__name__)


# START_BLOCK_COLLECT_FLAT
def collect_chapters(use_graph=True):
    """Собрать плоский список глав для генерации.

    Priority:
    1. Если use_graph=True — попробовать прочитать из knowledge-graph.xml
    2. Fallback — динамическое сканирование файловой системы docs/
    """
    if use_graph:
        graph_chapters = chapters_from_graph()
        if graph_chapters:
            logger.info("[Structure][collect_chapters][BLOCK_COLLECT_FLAT] source=graph count=%d", len(graph_chapters))
            return graph_chapters

    nodes = scan_docs_directory()
    flat = flatten_chapters(nodes)

    existing_ids = set()
    for ch in flat:
        mid = derive_module_id(ch["heading"], existing_ids)
        existing_ids.add(mid)
        ch["module_id"] = mid

    logger.info("[Structure][collect_chapters][BLOCK_COLLECT_FLAT] source=discovery count=%d", len(flat))
    return flat
# END_BLOCK_COLLECT_FLAT
