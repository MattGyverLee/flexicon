#
#   catalog.py
#
#   Module: Catalog file discovery and XML parsing helpers for FieldWorks
#           catalog XML formats.
#
#           Phase 5a: GOLDEtic shape used by the FW Templates/GOLDEtic.xml
#           POS catalog:
#
#               <eticPOSList>
#                 <item type="category" id="Adjective" guid="...">
#                   <abbrev ws="en">adj</abbrev>
#                   <term ws="en">Adjective</term>
#                   <def ws="en">An adjective is ...</def>
#                   <item type="category" ...>  <!-- nested -->
#                 </item>
#                 ...
#               </eticPOSList>
#
#           Phase 5b: eticGlossList shape used by the FW MGA gloss-list
#           catalogs (e.g. Language Explorer/MGA/GlossLists/
#           PhonFeatsEticGlossList.xml):
#
#               <eticGlossList>
#                 <item type="group" id="gPAPhonFeatures" guid="...">
#                   ...
#                   <item type="feature" id="fPAConsonantal" guid="...">
#                     <abbrev ws="en">cons</abbrev>
#                     <term ws="en">consonantal</term>
#                     <item type="value" id="vPAConsonantalPositive" ...>
#                       <abbrev ws="en">+</abbrev>
#                       <term ws="en">positive</term>
#                     </item>
#                     ...
#                   </item>
#                 </item>
#               </eticGlossList>
#
#           Other FW catalog shapes (LocalizedLists, semantic-domain catalogs,
#           etc.) will be added in later phases.
#
#           See docs/CATALOG_CONVENTIONS.md for the prefix policy each
#           catalog uses when writing CatalogSourceId.
#
#   Platform: Python (stdlib only; no FieldWorks/.NET dependency)
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .. import FLExGlobals


# --- Public dataclasses ------------------------------------------------------


@dataclass
class CatalogEntry:
    """
    One <item type="category"> from the GOLDEtic catalog.

    Attributes:
        id:       The catalog id, e.g. "Adjective". This is the suffix of
                  the canonical CatalogSourceId ("GOLD:Adjective").
        guid:     The canonical FW GUID for this category, as a string.
                  e.g. "30d07580-5052-4d91-bc24-469b8b2d7df9".
        abbrev:   Map of writing-system tag -> abbreviation string,
                  e.g. {"en": "adj", "fr": "adj", "ko": "형"}.
        term:     Map of writing-system tag -> name/term string,
                  e.g. {"en": "Adjective", "fr": "Adjectif"}.
        def_:     Map of writing-system tag -> definition string. Note
                  the trailing underscore: "def" is a Python keyword.
        children: List of nested CatalogEntry items (sub-categories
                  in the catalog hierarchy).
    """

    id: str
    guid: str
    abbrev: Dict[str, str] = field(default_factory=dict)
    term: Dict[str, str] = field(default_factory=dict)
    def_: Dict[str, str] = field(default_factory=dict)
    children: List["CatalogEntry"] = field(default_factory=list)


@dataclass
class CatalogImportResult:
    """
    Summary of what happened during a catalog import.

    Attributes:
        created_count: Number of new POSs created.
        skipped_count: Number of catalog entries skipped because a POS
                       with the same canonical GUID already exists.
        created_guids: Canonical GUIDs (as strings) for the POSs that
                       were created. Useful for verification and tests.
        warnings:      Human-readable warnings (e.g. WS tags present in
                       the catalog but missing from the project).
    """

    created_count: int = 0
    skipped_count: int = 0
    created_guids: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# --- File discovery ----------------------------------------------------------


def find_catalog_file(filename, subdir="Templates"):
    """
    Locate a catalog XML file under the FieldWorks install.

    Uses FLExGlobals.FWCodeDir (resolved during FLEx init from the
    Windows registry) so it works against whatever FW install the
    user actually has. Does not hard-code "C:/Program Files/SIL/...".

    Args:
        filename (str): The catalog filename, e.g. "GOLDEtic.xml".
        subdir (str):   Relative subdirectory under FWCodeDir; default
                        "Templates" (used for GOLDEtic.xml). For MGA
                        gloss lists, pass "Language Explorer/MGA/GlossLists".
                        Forward slashes are converted to OS-native
                        separators by os.path.join.

    Returns:
        str: Absolute path to the catalog file.

    Raises:
        RuntimeError: If FLExGlobals.FWCodeDir has not been initialised
                      (caller must have imported flexlibs2 first).
        FileNotFoundError: If the file does not exist at the expected path.
    """
    if FLExGlobals.FWCodeDir is None:
        raise RuntimeError(
            "FLExGlobals.FWCodeDir is not set; "
            "import flexlibs2 (or call FLExGlobals.InitialiseFWGlobals()) first."
        )

    # Normalize slashes in subdir so callers can pass "a/b/c" portably.
    subdir_parts = [p for p in subdir.replace("\\", "/").split("/") if p]
    path = os.path.join(FLExGlobals.FWCodeDir, *subdir_parts, filename)
    if not os.path.isfile(path):
        raise FileNotFoundError(
            "Catalog file not found at expected location: {}".format(path)
        )
    return path


# --- XML parsing -------------------------------------------------------------


def _parse_item(elem):
    """
    Recursively parse one <item type="category"> element into a
    CatalogEntry. Non-category items are ignored. Children are walked
    depth-first so the returned tree mirrors the on-disk hierarchy.
    """
    entry = CatalogEntry(
        id=elem.get("id") or "",
        guid=elem.get("guid") or "",
    )

    for child in elem:
        tag = child.tag
        if tag == "abbrev":
            ws = child.get("ws") or ""
            if ws and child.text:
                entry.abbrev[ws] = child.text
        elif tag == "term":
            ws = child.get("ws") or ""
            if ws and child.text:
                entry.term[ws] = child.text
        elif tag == "def":
            ws = child.get("ws") or ""
            if ws and child.text:
                entry.def_[ws] = child.text
        elif tag == "item" and child.get("type") == "category":
            entry.children.append(_parse_item(child))
        # Silently ignore unknown / non-category children (source,
        # citation, etc.) - they aren't part of the Phase 5a MVP.

    return entry


def parse_etic_catalog(path):
    """
    Parse a GOLDEtic-shaped POS catalog XML file into a tree of
    CatalogEntry objects.

    Args:
        path (str): Absolute path to GOLDEtic.xml.

    Returns:
        list[CatalogEntry]: The top-level catalog entries. Nested
        sub-categories are reachable via each entry's `.children`.

    Notes:
        - The root element is <eticPOSList>; we walk its direct
          <item type="category"> children and recurse from there.
        - Other root shapes are not supported by this function.
    """
    tree = ET.parse(path)
    root = tree.getroot()

    if root.tag != "eticPOSList":
        raise ValueError(
            "Expected root <eticPOSList>, got <{}>; this parser only "
            "handles the GOLDEtic shape.".format(root.tag)
        )

    entries = []
    for item in root.findall("item"):
        if item.get("type") == "category":
            entries.append(_parse_item(item))
    return entries


# --- eticGlossList parsing (Phase 5b) ---------------------------------------


def _parse_gloss_item(elem, expected_type):
    """
    Parse one <item> element from an eticGlossList catalog as a
    CatalogEntry. Only the abbrev/term/def localised strings and any
    nested <item> children matching `expected_type` are captured.

    `expected_type` is the type attribute value to recurse into for
    children: for a "feature" element, child items are "value"s; for
    a "value" element there are no expected children (pass None).
    """
    entry = CatalogEntry(
        id=elem.get("id") or "",
        guid=elem.get("guid") or "",
    )

    for child in elem:
        tag = child.tag
        if tag == "abbrev":
            ws = child.get("ws") or ""
            if ws and child.text:
                entry.abbrev[ws] = child.text
        elif tag == "term":
            ws = child.get("ws") or ""
            if ws and child.text:
                entry.term[ws] = child.text
        elif tag == "def":
            ws = child.get("ws") or ""
            if ws and child.text:
                entry.def_[ws] = child.text
        elif tag == "item" and expected_type and child.get("type") == expected_type:
            # Value items have no further children we care about.
            entry.children.append(_parse_gloss_item(child, None))
        # Silently ignore <citation>, <fs> (FW UI's encoded feature structure
        # for values), <source>, and any other extraneous markup - they
        # aren't part of the Phase 5b import contract.

    return entry


def parse_etic_gloss_list(path):
    """
    Parse a PhonFeatsEticGlossList-shaped catalog (root <eticGlossList>)
    into a flat list of feature CatalogEntry objects.

    Items have type="group" | "fsType" | "feature" | "value":
        - "group" entries are organizational only (not representable in
          LCM). They are skipped at every level, but the parser recurses
          INTO them so any features they contain still get returned.
        - "fsType" entries are agreement-category containers (e.g.
          ``tCommonAgr`` holds the Bantu number features ``fBantuSg``,
          ``fBantuPl``, ``fBantuMany``). Like "group" they are
          organizational and are not themselves CatalogEntry items, but
          the parser recurses INTO them so the features they hold get
          returned. (issue #192)
        - "feature" entries become CatalogEntry items in the returned
          list. Each feature's value children are attached to its
          `.children` list.
        - "value" entries become CatalogEntry children of their parent
          feature entry.

    Args:
        path (str): Absolute path to e.g. PhonFeatsEticGlossList.xml.

    Returns:
        list[CatalogEntry]: Flat list of feature entries with their
        value entries attached as `.children`. Group structure is
        flattened away.

    Raises:
        ValueError: If the root element is not <eticGlossList>.
    """
    tree = ET.parse(path)
    root = tree.getroot()

    if root.tag != "eticGlossList":
        raise ValueError(
            "Expected root <eticGlossList>, got <{}>; this parser only "
            "handles the eticGlossList shape.".format(root.tag)
        )

    features = []

    def _walk(items):
        for item in items:
            t = item.get("type")
            if t == "feature":
                features.append(_parse_gloss_item(item, "value"))
            elif t in ("group", "fsType"):
                # Organizational containers; descend into their
                # children but don't emit a CatalogEntry for the
                # container itself. fsType wraps agreement-category
                # feature sets (e.g. tCommonAgr holds the Bantu number
                # features). (issue #192)
                _walk(item.findall("item"))
            # Any other top-level type is silently ignored.

    _walk(root.findall("item"))
    return features


# --- BasicIPAInfo parsing (Phase 6d) ----------------------------------------


def _normalize_codepoints(raw):
    """
    Canonicalise a ``unicodeCodePoints`` attribute value for use as a
    stable dedup key.

    The catalog format encodes multi-codepoint segments (affricates,
    clicks, pre-nasalized stops) as a whitespace-separated list, e.g.
    ``"u0074 u0283"`` for /tʃ/. Without normalization the raw string is
    fragile as a dedup key: extra whitespace ("u0074  u0283"), variant
    ordering ("u0283 u0074"), or trailing spaces would all produce
    distinct keys for what is the same segment.

    Canonicalises by splitting on whitespace (collapsing runs), sorting
    the codepoint tokens lexicographically, and joining back with single
    spaces. Single-codepoint ids ("u0061") round-trip unchanged.

    (issue #141 part 2)
    """
    return " ".join(sorted(raw.split()))


@dataclass
class SegmentDefinition:
    """
    One <SegmentDefinition> from the BasicIPAInfo.xml catalog.

    BasicIPAInfo.xml ships with FW under Templates/BasicIPAInfo.xml. Unlike
    GOLDEtic / eticGlossList catalogs, segments have NO per-entry GUIDs:
    the only stable identifier is ``code_point_id`` (e.g. "u0061"), which
    the importer uses to dedup within a single pass but cannot use for
    cross-import idempotency.

    Attributes:
        code_point_id: Value of the ``unicodeCodePoints`` attribute on the
                       (first) ``<Representation>`` element, e.g. ``"u0061"``
                       for the segment "a".
        representation: The element text of the (first) ``<Representation>``,
                        e.g. ``"a"``. This is what the importer writes into
                        ``IPhPhoneme.Name`` and ``BasicIPASymbol``.
        descriptions:  Map of ``lang`` attribute -> description text,
                       e.g. ``{"en": "Open front unrounded vowel"}``.
        feature_pairs: List of ``(feature_id, value_id)`` tuples from the
                       ``<Features>/<FeatureValuePair>`` children. Both ids
                       reference PhonFeats catalog entries (e.g.
                       ``("fPAConsonantal", "vPAConsonantalNegative")``).
                       Empty list when the segment has ``<Features/>``.
    """

    code_point_id: str
    representation: str
    descriptions: Dict[str, str] = field(default_factory=dict)
    feature_pairs: List[tuple] = field(default_factory=list)


def parse_basic_ipa_info(path):
    """
    Parse a BasicIPAInfo.xml-shaped segment catalog (root
    ``<SegmentDefinitions>``) into a flat list of SegmentDefinition
    objects.

    Args:
        path (str): Absolute path to BasicIPAInfo.xml.

    Returns:
        list[SegmentDefinition]: One entry per ``<SegmentDefinition>``.
        Order in the returned list matches order in the source file (FW
        ships the catalog with a meaningful order: tones first, then
        vowels and consonants).

    Raises:
        ValueError: If the root element is not ``<SegmentDefinitions>``.

    Notes:
        - Only the FIRST ``<Representation>`` child is captured. The stock
          catalog has exactly one per segment; multi-representation
          segments would need a richer dataclass.
        - Description ``lang`` tags use the lowercase short form
          ("en", "es", "fr", ...). The catalog ships English plus partial
          Spanish; other languages may be sparse.
        - Segments with empty ``<Features/>`` (the tone entries at the
          head of the file) end up with ``feature_pairs == []``.
    """
    tree = ET.parse(path)
    root = tree.getroot()

    if root.tag != "SegmentDefinitions":
        raise ValueError(
            "Expected root <SegmentDefinitions>, got <{}>; this parser only "
            "handles the BasicIPAInfo shape.".format(root.tag)
        )

    result = []
    for sd in root.findall("SegmentDefinition"):
        rep_elem = sd.find("Representations/Representation")
        if rep_elem is None:
            # Defensive: skip malformed entries silently rather than
            # aborting an import. The stock catalog is well-formed; this
            # only matters for user-edited / partial files.
            continue
        rep_text = (rep_elem.text or "").strip()
        code_id = _normalize_codepoints(rep_elem.get("unicodeCodePoints") or "")

        descs = {}
        for d in sd.findall("Descriptions/Description"):
            lang = d.get("lang") or ""
            if lang and d.text:
                descs[lang] = d.text

        pairs = []
        for fv in sd.findall("Features/FeatureValuePair"):
            feat_id = fv.get("feature") or ""
            val_id = fv.get("value") or ""
            if feat_id and val_id:
                pairs.append((feat_id, val_id))

        result.append(
            SegmentDefinition(
                code_point_id=code_id,
                representation=rep_text,
                descriptions=descs,
                feature_pairs=pairs,
            )
        )

    return result


# --- Tree navigation ---------------------------------------------------------


_KNOWN_CATALOG_PREFIXES = ("GOLD", "PHON", "INFL")


def _strip_catalog_prefix(source_id):
    """
    Accept either a bare id ("Adjective", "fPAConsonantal") or a prefixed
    catalog source id ("GOLD:Adjective", "PHON:fPAConsonantal") and return
    the bare id. Case-sensitive on the id portion; the prefix match is
    case-insensitive. Unknown prefixes are passed through unchanged.
    """
    if not source_id:
        return ""
    head, sep, tail = source_id.partition(":")
    if sep and head.upper() in _KNOWN_CATALOG_PREFIXES:
        return tail
    return source_id


def find_catalog_entry(entries, source_id):
    """
    Walk a list of CatalogEntry trees (depth-first) and return the
    entry whose id matches `source_id`. Known catalog prefixes
    ("GOLD:", "PHON:") are stripped before comparison so both
    "GOLD:Adjective" and "Adjective" work.

    Args:
        entries (list[CatalogEntry]): Result of parse_etic_catalog() or
                                       parse_etic_gloss_list().
        source_id (str): Catalog source id, with or without a known
                         prefix.

    Returns:
        CatalogEntry or None: The matching entry, or None if no match.
    """
    target = _strip_catalog_prefix(source_id)
    if not target:
        return None

    def _walk(items):
        for it in items:
            if it.id == target:
                return it
            if it.children:
                hit = _walk(it.children)
                if hit is not None:
                    return hit
        return None

    return _walk(entries)


def count_catalog_entries(entries):
    """
    Count all CatalogEntry items in a forest, including nested children.

    Convenience helper for tests / smoke checks. GOLDEtic.xml has
    16 top-level entries and 58 entries total.

    Args:
        entries (list[CatalogEntry]): Result of parse_etic_catalog().

    Returns:
        int: Total number of entries across the tree.
    """
    total = 0

    def _walk(items):
        nonlocal total
        for it in items:
            total += 1
            if it.children:
                _walk(it.children)

    _walk(entries)
    return total
