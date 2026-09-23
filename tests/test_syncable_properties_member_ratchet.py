#
#   test_syncable_properties_member_ratchet.py
#
#   Class: TestSyncablePropertiesMemberRatchet
#          Offline ratchet guard for issue #325: every field name referenced
#          as hasattr(item, "<name>") inside a GetSyncableProperties method
#          must exist as a property on the target LCM interface in the
#          liblcm_baseline snapshot.  A miss means the hasattr guard is
#          always False at runtime and the key is silently dead -- the same
#          class of bug that R7 fixed for DoNotShowMainEntryInRC on ILexSense.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import json
import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BASELINE_PATH = REPO_ROOT / "tests" / "contract" / "snapshots" / "liblcm_baseline.json"
OPS_DIR = REPO_ROOT / "flexicon" / "code"

# ---------------------------------------------------------------------------
# Interface mapping
#
# Maps each *Operations.py filename to the primary LCM interface type whose
# properties the GetSyncableProperties `item` argument exposes.  Only files
# that have a GetSyncableProperties implementation and whose item type is
# unambiguous belong here.
# ---------------------------------------------------------------------------
_OPS_INTERFACE_MAP: dict[str, str] = {
    "EtymologyOperations.py":      "ILexEtymology",
    "ExampleOperations.py":        "ILexExampleSentence",
    "LexEntryOperations.py":       "ILexEntry",
    "LexReferenceOperations.py":   "ILexReference",
    "LexSenseOperations.py":       "ILexSense",
    "PronunciationOperations.py":  "ILexPronunciation",
    "SemanticDomainOperations.py": "ICmSemanticDomain",
    "VariantOperations.py":        "ILexEntryRef",
    "AnthropologyOperations.py":   "ICmAnthroItem",
    "DiscourseOperations.py":      "IDsConstChart",
    "ParagraphOperations.py":      "IStTxtPara",
    "SegmentOperations.py":        "ISegment",
    "TextOperations.py":           "IText",
    "WfiAnalysisOperations.py":    "IWfiAnalysis",
    "WfiGlossOperations.py":       "IWfiGloss",
    "WfiMorphBundleOperations.py": "IWfiMorphBundle",
    "WordformOperations.py":       "IWfiWordform",
    "MediaOperations.py":          "ICmFile",
}

# ---------------------------------------------------------------------------
# Allowlist
#
# Fields that are known to be absent from the snapshot but are legitimately
# allowlisted.  Each entry carries a reason comment that cites the ruling
# or T0 evidence.
#
# Key: (ops_filename, interface_name, field_name)
# Value: human-readable reason
# ---------------------------------------------------------------------------
_ALLOWLIST: dict[tuple[str, str, str], str] = {
    # ICmMediaContainer is absent from the baseline entirely because no live
    # project had media configured during T0 reflection (issue #325 T0,
    # live-T0-media-raw.json).  The hasattr guard on MediaFilesOA accesses
    # IText, which IS in the baseline; the container fields are reached via
    # the concrete cast, so they do not appear as item-level hasattr in the
    # current code.  This entry is a placeholder for if MediaOperations grows
    # a media-container GetSyncableProperties in the future.
    # (No current hit; retained for documentation purposes only.)

}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_HASATTR_ITEM_RE = re.compile(r'hasattr\(item,\s*["\'](\w+)["\']\)')


def _load_baseline() -> dict[str, list[str]]:
    """Return {interface_name: [property_name, ...]} from the baseline JSON."""
    data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    result = {}
    for type_name, type_info in data.get("types", {}).items():
        if isinstance(type_info, dict):
            result[type_name] = type_info.get("properties", [])
    return result


def _extract_gsp_body(source: str) -> str:
    """Return the source text of the GetSyncableProperties method body.

    Uses a line-based heuristic: finds the ``def GetSyncableProperties(``
    signature line, then captures lines until we encounter another ``def ``
    or ``class `` at the same or lesser indentation (the method boundary).
    Returns an empty string if the method is not found.
    """
    lines = source.splitlines()
    start_idx = None
    indent = None

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("def GetSyncableProperties("):
            start_idx = i
            indent = len(line) - len(stripped)
            break

    if start_idx is None:
        return ""

    body_lines = [lines[start_idx]]
    for line in lines[start_idx + 1:]:
        stripped = line.lstrip()
        if not stripped:
            body_lines.append(line)
            continue
        current_indent = len(line) - len(stripped)
        # A new def/class at the same or lesser indentation ends the method.
        if current_indent <= indent and (
            stripped.startswith("def ") or stripped.startswith("class ")
            or stripped.startswith("@")
        ):
            break
        body_lines.append(line)

    return "\n".join(body_lines)


def _collect_hasattr_fields(ops_file: pathlib.Path) -> list[str]:
    """Return deduplicated list of field names from hasattr(item, ...) calls
    inside GetSyncableProperties."""
    source = ops_file.read_text(encoding="utf-8")
    body = _extract_gsp_body(source)
    if not body:
        return []
    fields = _HASATTR_ITEM_RE.findall(body)
    return list(dict.fromkeys(fields))  # deduplicate, preserve order


# ---------------------------------------------------------------------------
# Parametrized test data
# ---------------------------------------------------------------------------

def _build_test_cases() -> list[tuple[str, str, str]]:
    """Return (ops_filename, interface_name, field_name) for every
    hasattr(item, field) in a GetSyncableProperties body that is NOT
    in the allowlist and whose interface IS in the baseline."""
    cases = []
    for fname, iface in _OPS_INTERFACE_MAP.items():
        ops_file = next(OPS_DIR.rglob(fname), None)
        if ops_file is None:
            continue
        for field in _collect_hasattr_fields(ops_file):
            cases.append((fname, iface, field))
    return cases


_ALL_CASES = _build_test_cases()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSyncablePropertiesMemberRatchet:
    """
    For every GetSyncableProperties implementation, assert that each field
    referenced as hasattr(item, "<name>") exists on the target interface in
    the liblcm_baseline snapshot.

    A miss means the hasattr guard is always False at runtime and the sync
    key is silently dead -- the same defect class fixed by R7 (issue #325).
    """

    @pytest.mark.parametrize("ops_filename,interface,field", _ALL_CASES)
    def test_hasattr_field_exists_on_interface(
        self, ops_filename: str, interface: str, field: str
    ):
        """Each hasattr(item, field) in GetSyncableProperties must exist on
        the target LCM interface in the baseline snapshot, or be explicitly
        allowlisted with a documented reason."""
        key = (ops_filename, interface, field)
        if key in _ALLOWLIST:
            reason = _ALLOWLIST[key]
            pytest.skip(f"Allowlisted: {reason}")

        baseline = _load_baseline()
        if interface not in baseline:
            pytest.skip(
                f"{interface} is absent from the baseline snapshot "
                f"(no live instances available during T0; cite: "
                f"specs/325-syncable-properties/evidence/live-T0-reflection.md)"
            )

        props = baseline[interface]
        assert field in props, (
            f"MISS -- {ops_filename} / {interface}: "
            f"hasattr(item, '{field}') in GetSyncableProperties but "
            f"'{field}' is absent from {interface} in the baseline snapshot. "
            f"The hasattr guard is always False at runtime; this is a dead sync key. "
            f"Either the field name is wrong or the interface does not expose it. "
            f"See issue #325 R7 for the remediation pattern."
        )

    def test_r7_donotshowmainentryinrc_removed_from_lexsense_gsp(self):
        """R7 regression guard: DoNotShowMainEntryInRC must NOT appear as a
        hasattr(item, ...) target in LexSenseOperations.GetSyncableProperties.

        T0 confirmed ILexSense has no DoNotShowMainEntryInRC in either the
        static interface or the live implementation.  The field was removed
        per ruling R7 (issue #325).
        """
        ops_file = next(OPS_DIR.rglob("LexSenseOperations.py"), None)
        assert ops_file is not None, "LexSenseOperations.py not found"

        fields = _collect_hasattr_fields(ops_file)
        assert "DoNotShowMainEntryInRC" not in fields, (
            "DoNotShowMainEntryInRC was found in LexSenseOperations."
            "GetSyncableProperties hasattr calls.  R7 requires it to be "
            "absent (ILexSense does not expose this field on FieldWorks 9+). "
            "See issue #325 R7."
        )

    def test_donotpublishinrc_still_present_in_lexsense_gsp(self):
        """Regression guard: DoNotPublishInRC (a different field) must still
        appear in LexSenseOperations.GetSyncableProperties -- R7 must not have
        over-deleted."""
        ops_file = next(OPS_DIR.rglob("LexSenseOperations.py"), None)
        assert ops_file is not None, "LexSenseOperations.py not found"

        fields = _collect_hasattr_fields(ops_file)
        assert "DoNotPublishInRC" in fields, (
            "DoNotPublishInRC is missing from LexSenseOperations."
            "GetSyncableProperties hasattr calls.  It is a valid ILexSense "
            "field and must remain.  Check that R7 did not over-delete."
        )

    def test_allowlist_entries_are_still_needed(self):
        """Every allowlist entry must correspond to an actual hasattr(item, ...)
        call in the relevant GetSyncableProperties body.  Stale entries must
        be removed to keep the ratchet honest."""
        stale = []
        for (ops_fname, _iface, field), reason in _ALLOWLIST.items():
            ops_file = next(OPS_DIR.rglob(ops_fname), None)
            if ops_file is None:
                stale.append(
                    f"({ops_fname!r}, {field!r}): file not found -- "
                    f"drop allowlist entry"
                )
                continue
            fields = _collect_hasattr_fields(ops_file)
            if field not in fields:
                stale.append(
                    f"({ops_fname!r}, {field!r}): field no longer appears "
                    f"in GetSyncableProperties -- drop allowlist entry"
                )

        assert not stale, (
            "Stale allowlist entries in test_syncable_properties_member_ratchet.py:\n  "
            + "\n  ".join(stale)
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
