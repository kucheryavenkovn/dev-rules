# FILE: src/types.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Общие frozen dataclass-типы данных для всех модулей: ChapterInfo, ModuleInfo, GraceModule
#   SCOPE: Только определения типов и их утилиты. Без бизнес-логики.
#   DEPENDS: none
#   LINKS: M-TYPES
#   ROLE: TYPES
#   MAP_MODE: EXPORTS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   ChapterInfo - frozen dataclass: структура главы (heading, source, depth, position, parent_heading, is_container, rel_path, module_id)
#   ModuleInfo - frozen dataclass: структура модуля (id, heading, type, para_start, para_end, elements, subsections, parent, parent_heading)
#   GraceModule - frozen dataclass: структура grace-модуля для XML-инъекции
# END_MODULE_MAP

from dataclasses import dataclass, field, replace
from typing import Optional


@dataclass(frozen=True)
class ChapterInfo:
    heading: str
    source: Optional[str] = None
    depth: int = 0
    position: float = 0.0
    parent_heading: Optional[str] = None
    is_container: bool = False
    rel_path: str = ""
    module_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "heading": self.heading,
            "source": self.source,
            "depth": self.depth,
            "position": self.position,
            "parent_heading": self.parent_heading,
            "is_container": self.is_container,
            "rel_path": self.rel_path,
            "module_id": self.module_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ChapterInfo":
        return cls(
            heading=d.get("heading", ""),
            source=d.get("source"),
            depth=d.get("depth", 0),
            position=d.get("position", 0.0),
            parent_heading=d.get("parent_heading"),
            is_container=d.get("is_container", False),
            rel_path=d.get("rel_path", ""),
            module_id=d.get("module_id"),
        )

    def with_module_id(self, module_id: str) -> "ChapterInfo":
        return replace(self, module_id=module_id)


@dataclass(frozen=True)
class ModuleInfo:
    id: str
    heading: str
    type: str = "NARRATIVE"
    para_start: int = 0
    para_end: int = 0
    elements: tuple = field(default_factory=tuple)
    subsections: tuple = field(default_factory=tuple)
    parent: Optional[str] = None
    parent_heading: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "heading": self.heading,
            "type": self.type,
            "para_start": self.para_start,
            "para_end": self.para_end,
            "elements": list(self.elements),
            "subsections": list(self.subsections),
            "parent": self.parent,
            "parent_heading": self.parent_heading,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ModuleInfo":
        return cls(
            id=d.get("id", ""),
            heading=d.get("heading", ""),
            type=d.get("type", "NARRATIVE"),
            para_start=d.get("para_start", 0),
            para_end=d.get("para_end", 0),
            elements=tuple(d.get("elements", ())),
            subsections=tuple(d.get("subsections", ())),
            parent=d.get("parent"),
            parent_heading=d.get("parent_heading"),
        )


@dataclass(frozen=True)
class GraceModule:
    id: str
    heading: str
    type: str
    bookmark: str
    para_start: int = 0
    para_end: int = 0
    elements: tuple = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "heading": self.heading,
            "type": self.type,
            "bookmark": self.bookmark,
            "para_start": self.para_start,
            "para_end": self.para_end,
            "elements": list(self.elements),
        }
