# FILE: src/grace_injector.py
# VERSION: 1.1.0
# START_MODULE_CONTRACT
#   PURPOSE: Инъекция 5 GRACE XML-частей и парных закладок в .docx архив
#   SCOPE: inject_grace_parts, make_grace_manifest, make_grace_instructions, make_grace_contracts, make_grace_verification
#   DEPENDS: M-CONFIG, M-GRAPHSYNC, M-TYPES
#   LINKS: M-GRACE
#   ROLE: RUNTIME
#   MAP_MODE: EXPORTS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   inject_grace_parts - распаковать .docx, внедрить GRACE XML + закладки, упаковать обратно
#   make_grace_manifest - генерация grace-manifest.xml
#   make_grace_instructions - генерация grace-instructions.xml
#   make_grace_contracts - генерация grace-contracts.xml
#   make_grace_verification - генерация grace-verification.xml
# END_MODULE_MAP

import zipfile
import shutil
import tempfile
import logging
from pathlib import Path

from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from src.config import DOC_NAME, DOC_VERSION, GRACE_VERSION
from src.graph_sync import build_grace_graph_xml
from src.types import ModuleInfo

logger = logging.getLogger(__name__)


def _as_dict(mod):
    if isinstance(mod, ModuleInfo):
        return mod.to_dict()
    return mod


GRACE_PART_NAMES = [
    "grace-manifest.xml",
    "grace-instructions.xml",
    "grace-graph.xml",
    "grace-contracts.xml",
    "grace-verification.xml",
]


# START_BLOCK_MANIFEST
def make_grace_manifest(modules_info, today_str):
    parts_xml = ""
    for i, (fname, purpose) in enumerate([
        ("word/grace-manifest.xml", "Discovery beacon"),
        ("word/grace-instructions.xml", "Agent behavioral rules"),
        ("word/grace-graph.xml", "Document module map with element inventory"),
        ("word/grace-contracts.xml", "Per-module and per-type editing rules"),
        ("word/grace-verification.xml", "Integrity checks"),
    ], 1):
        parts_xml += f'    <part-{i}><file>{fname}</file><purpose>{purpose}</purpose><read-order>{i}</read-order></part-{i}>\n'

    steps_xml = ""
    for i, step in enumerate([
        "Unpack the .docx",
        "Read word/grace-manifest.xml",
        "Read word/grace-instructions.xml",
        "Read word/grace-graph.xml — locate target module",
        "Read word/grace-contracts.xml — check TypeContracts",
        "Navigate via bookmark name or paragraph range",
        "Perform edit according to contract rules",
        "Run verification from word/grace-verification.xml",
        "Pack the .docx back",
    ], 1):
        steps_xml += f'    <step-{i}>{step}</step-{i}>\n'

    manifest = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<GraceManifest VERSION="{GRACE_VERSION}" SCHEMA="grace-docx">
  <document-name>{DOC_NAME}</document-name>
  <document-version>{DOC_VERSION}</document-version>
  <grace-version>{GRACE_VERSION}</grace-version>
  <created>{today_str}</created>
  <last-updated>{today_str}</last-updated>
  <Parts>
{parts_xml}  </Parts>
  <Protocol>
{steps_xml}  </Protocol>
  <EditPolicy>
    <output-mode>new-version</output-mode>
  </EditPolicy>
  <BookmarkConvention>
    <pattern>GRACE_{{MODULE-ID}}</pattern>
    <description>Each H1 section gets a w:bookmarkStart/w:bookmarkEnd pair named GRACE_{{MODULE-ID}}.</description>
  </BookmarkConvention>
</GraceManifest>'''
    logger.debug("[GraceInjector][make_grace_manifest][BLOCK_MANIFEST] modules=%d", len(modules_info))
    return manifest
# END_BLOCK_MANIFEST


# START_BLOCK_INSTRUCTIONS
def make_grace_instructions():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<GraceInstructions VERSION="3.0.0">
  <CorePrinciples>
    <principle-1 name="contract-first">Before modifying any element, read its TypeContract in grace-contracts.xml, then check ModuleContract for overrides.</principle-1>
    <principle-2 name="bookmark-integrity">GRACE bookmarks are navigation anchors. They must remain paired and wrap the correct section.</principle-2>
    <principle-3 name="graph-is-current">When you add/remove/reorder content, update grace-graph.xml so future agents can navigate deterministically.</principle-3>
    <principle-4 name="verify-after-edit">After ANY edit, run the verification protocol from grace-verification.xml. If any hard-severity check fails, rollback.</principle-4>
    <principle-5 name="surgical-edits">Only change what is requested. Do not reformat, restyle, or clean up.</principle-5>
    <principle-6 name="element-type-awareness">Before editing a table or chart, check its type in ELEMENTS.</principle-6>
  </CorePrinciples>
  <EditRules>
    <rule severity="hard">Never modify w:rsidR, w:rsidRDefault, w14:paraId, w14:textId on existing elements</rule>
    <rule severity="hard">New paragraphs/runs must use same w:pStyle/w:rPr as siblings</rule>
    <rule severity="hard">Do not add/remove/reorder table columns</rule>
    <rule severity="hard">Do not promote H2 to H1 or demote H1 to H2</rule>
    <rule severity="hard">Recalculate para-range for ALL affected modules when paragraphs added/removed</rule>
    <rule severity="soft">Prefer append over insert</rule>
    <rule severity="soft">Batch must-sync updates in one pass</rule>
  </EditRules>
  <AntiPatterns>
    <item>Do not pretty-print document.xml</item>
    <item>Do not remove or rename GRACE_* bookmarks</item>
    <item>Do not delete grace-*.xml files</item>
    <item>Do not modify content outside requested scope</item>
  </AntiPatterns>
</GraceInstructions>'''
# END_BLOCK_INSTRUCTIONS


# START_BLOCK_CONTRACTS
def make_grace_contracts(modules_info):
    module_contracts = ""
    for mod in modules_info:
        m = _as_dict(mod)
        parent_type = "C-NARRATIVE" if m["type"] in ("NARRATIVE", "META", "NAVIGATION", "REFERENCE") else \
                     "C-TABLE-DATA" if m["type"] == "DATA" else "C-MIXED"
        module_contracts += f'''
    <C-{m["id"]} inherits="{parent_type}">
      <description>{m["heading"]} — {m["type"]}-type section</description>
      <can-edit>
        <item>Add paragraphs after existing content, modify text runs</item>
      </can-edit>
      <cannot-edit>
        <item>Change heading styles or structure</item>
      </cannot-edit>
    </C-{m["id"]}>'''

    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<GraceContracts VERSION="3.0.0">
  <GlobalRules>
    <rule severity="hard">Never remove or merge GRACE bookmark pairs</rule>
    <rule severity="hard">Table column structure is immutable</rule>
    <rule severity="hard">CHART-IMAGE and VISUAL-IMAGE are readonly</rule>
    <rule severity="soft">Prefer adding new paragraphs over modifying existing ones</rule>
  </GlobalRules>
  <TypeContracts>
    <C-NARRATIVE>
      <description>Prose sections: paragraphs, bullets, numbered lists</description>
      <can-edit>Add paragraphs after existing content, modify text runs</can-edit>
      <cannot-edit>Change heading styles, modify list numbering format</cannot-edit>
    </C-NARRATIVE>
    <C-TABLE-DATA>
      <description>Tables with a header row and data rows</description>
      <can-edit>Add rows at the end, update cell values in data rows</can-edit>
      <cannot-edit>Modify header row, add or remove columns</cannot-edit>
    </C-TABLE-DATA>
    <C-TABLE-STRUCT>
      <description>Structural tables: RACI matrices, comparison grids</description>
      <can-edit>Update cell text values</can-edit>
      <cannot-edit>Add or remove rows or columns</cannot-edit>
    </C-TABLE-STRUCT>
    <C-MIXED>
      <description>Mixed prose and data content</description>
      <can-edit>Add paragraphs, update table data rows, modify prose text</can-edit>
      <cannot-edit>Change table headers, modify structure</cannot-edit>
    </C-MIXED>
  </TypeContracts>
  <ModuleContracts>{module_contracts}
  </ModuleContracts>
</GraceContracts>'''
# END_BLOCK_CONTRACTS


# START_BLOCK_VERIFICATION_XML
def make_grace_verification(num_modules):
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<GraceVerification VERSION="3.0.0">
  <StructuralInvariants>
    <invariant id="bookmark-balance" severity="hard">
      Count bookmarkStart with name starting "GRACE_". Count bookmarkEnd. Must be equal. Expected: {num_modules} pairs.
    </invariant>
    <invariant id="heading-hierarchy" severity="hard">
      For each H2, a preceding H1 must exist.
    </invariant>
    <invariant id="grace-xml-valid" severity="hard">
      All grace-*.xml files must parse as well-formed XML.
    </invariant>
    <invariant id="graph-covers-all-h1" severity="hard">
      Every H1 heading must have a matching module in grace-graph.xml. Expected: {num_modules}.
    </invariant>
    <invariant id="graph-synced-with-source" severity="hard">
      grace-graph.xml Modules must match docs/knowledge-graph.xml DocChapters.
    </invariant>
  </StructuralInvariants>
  <PostEditChecks>
    <check id="paragraph-range-accuracy">After changes, re-scan heading positions and update para-range.</check>
    <check id="bookmark-intact">After edits near bookmark boundary, verify pairing.</check>
    <check id="graph-source-sync">Verify grace-graph.xml source-graph points to docs/knowledge-graph.xml.</check>
  </PostEditChecks>
  <ValidationProtocol>
    <step>Run all StructuralInvariants before edit</step>
    <step>If any hard-severity fails — STOP</step>
    <step>Perform edit according to TypeContract</step>
    <step>Run all StructuralInvariants again</step>
    <step>Run relevant PostEditChecks</step>
    <step>If any hard check fails — ROLLBACK</step>
    <step>Update grace-graph.xml if structure changed</step>
    <step>Pack document</step>
  </ValidationProtocol>
</GraceVerification>'''
# END_BLOCK_VERIFICATION_XML


# START_BLOCK_INJECT
def inject_grace_parts(base_docx_path, grace_docx_path, modules_info,
                       total_paras, total_tables, total_h1, total_h2,
                       today_str):
    """Распаковать .docx, внедрить 5 GRACE XML + обновить Content_Types и rels, упаковать."""
    logger.info("[GraceInjector][inject_grace_parts][BLOCK_INJECT] base=%s modules=%d paras=%d tables=%d", base_docx_path.name, len(modules_info), total_paras, total_tables)
    tmp_dir = Path(tempfile.mkdtemp())
    grace_dir = tmp_dir / "word"
    grace_dir.mkdir(exist_ok=True)

    with zipfile.ZipFile(str(base_docx_path), "r") as z:
        z.extractall(str(tmp_dir))

    (grace_dir / "grace-manifest.xml").write_text(
        make_grace_manifest(modules_info, today_str), encoding="utf-8")
    (grace_dir / "grace-instructions.xml").write_text(
        make_grace_instructions(), encoding="utf-8")
    (grace_dir / "grace-graph.xml").write_text(
        build_grace_graph_xml(modules_info, total_paras, total_tables, total_h1, total_h2),
        encoding="utf-8")
    (grace_dir / "grace-contracts.xml").write_text(
        make_grace_contracts(modules_info), encoding="utf-8")
    (grace_dir / "grace-verification.xml").write_text(
        make_grace_verification(len(modules_info)), encoding="utf-8")

    ct_path = tmp_dir / "[Content_Types].xml"
    ct_content = ct_path.read_text(encoding="utf-8")
    grace_overrides = ""
    for name in GRACE_PART_NAMES:
        grace_overrides += f'<Override PartName="/word/{name}" ContentType="application/xml"/>\n'
    ct_content = ct_content.replace("</Types>", f"{grace_overrides}</Types>")
    ct_path.write_text(ct_content, encoding="utf-8")

    rels_path = tmp_dir / "word" / "_rels" / "document.xml.rels"
    if rels_path.exists():
        rels_content = rels_path.read_text(encoding="utf-8")
        grace_rels = ""
        for i, name in enumerate(GRACE_PART_NAMES, 1):
            rid = f"rIdGrace{i}"
            if rid not in rels_content:
                grace_rels += f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/customXml" Target="{name}"/>\n'
        rels_content = rels_content.replace("</Relationships>", f"{grace_rels}</Relationships>")
        rels_path.write_text(rels_content, encoding="utf-8")

    with zipfile.ZipFile(str(grace_docx_path), "w", zipfile.ZIP_DEFLATED) as zout:
        for file_path in sorted(tmp_dir.rglob("*")):
            if file_path.is_file():
                arcname = file_path.relative_to(tmp_dir)
                zout.write(str(file_path), str(arcname))

    shutil.rmtree(str(tmp_dir))
    logger.info("[GraceInjector][inject_grace_parts][BLOCK_INJECT] output=%s", grace_docx_path.name)
# END_BLOCK_INJECT


# START_BLOCK_INJECT_BOOKMARKS
def inject_bookmark_start(paragraph, bookmark_id, module_id):
    """Вставить bookmarkStart в параграф."""
    bm_start = OxmlElement("w:bookmarkStart")
    bm_start.set(qn("w:id"), str(bookmark_id))
    bm_start.set(qn("w:name"), f"GRACE_{module_id}")
    paragraph._element.insert(0, bm_start)


def inject_bookmark_end(doc, bookmark_id):
    """Вставить bookmarkEnd после последнего параграфа."""
    bm_end = OxmlElement("w:bookmarkEnd")
    bm_end.set(qn("w:id"), str(bookmark_id))
    last_para = doc.paragraphs[-1]._element
    last_para.addnext(bm_end)
# END_BLOCK_INJECT_BOOKMARKS
