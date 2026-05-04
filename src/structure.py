# FILE: src/structure.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Определение иерархии глав и сборка плоского списка для генерации
#   SCOPE: collect_chapters
#   DEPENDS: M-CONFIG (CHAPTERS)
#   LINKS: M-STRUCTURE
#   ROLE: RUNTIME
#   MAP_MODE: EXPORTS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   collect_chapters - рекурсивно собрать плоский список глав из OrderedDict
# END_MODULE_MAP

from src.config import CHAPTERS


# START_BLOCK_COLLECT_FLAT
def collect_chapters(chapters_dict=None, depth=0, parent_id=None, parent_heading=None):
    """Собрать плоский список глав для генерации из иерархического словаря."""
    if chapters_dict is None:
        chapters_dict = CHAPTERS
    result = []
    for heading, source in chapters_dict.items():
        if isinstance(source, str):
            result.append({
                "heading": heading,
                "source": source,
                "depth": depth,
                "parent_id": parent_id,
                "parent_heading": parent_heading,
            })
        elif isinstance(source, dict):
            result.append({
                "heading": heading,
                "source": None,
                "depth": depth,
                "parent_id": parent_id,
                "parent_heading": parent_heading,
                "is_container": True,
            })
            result.extend(collect_chapters(source, depth + 1, parent_id=heading, parent_heading=heading))
    return result
# END_BLOCK_COLLECT_FLAT
