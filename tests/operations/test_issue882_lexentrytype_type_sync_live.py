#
#   test_issue882_lexentrytype_type_sync_live.py
#
#   Issue #882: VariantOperations LexEntryType Name/Abbrev/Description/ReverseAbbr.
#   Verified on target_sandbox (tempdir copy only).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon.code.Shared.string_utils import normalize_text
from SIL.LCModel.Core.KernelInterfaces import ITsString


def _lex_entry_types(project):
    from flexicon.code.lcm_casting import cast_to_concrete

    found = []
    for raw in project.Variants.GetAllTypes():
        t = cast_to_concrete(raw)
        if getattr(t, "ClassName", None) == "LexEntryType":
            found.append(t)
    return found


@pytest.mark.requires_live_project
class TestIssue882LexEntryTypeSyncLive:

    def test_lex_entry_type_name_roundtrip(self, target_sandbox):
        p = target_sandbox
        types = _lex_entry_types(p)
        if len(types) < 2:
            pytest.skip("need two LexEntryType rows in VariantEntryTypesOA")

        src, dst = types[0], types[1]
        ws = p.project.DefaultAnalWs
        src_name = normalize_text(
            ITsString(src.Name.get_String(ws)).Text
        )
        if not src_name:
            pytest.skip("source LexEntryType Name empty in default analysis WS")

        props = p.Variants.GetTypeSyncableProperties(src)
        assert props.get("Name"), props

        p.Variants.ApplyTypeSyncableProperties(dst, {"Name": props["Name"]})
        dst_name = normalize_text(
            ITsString(dst.Name.get_String(ws)).Text
        )
        for ws_id, text in props["Name"].items():
            ws_handle = p.WritingSystems.Find(ws_id).Handle
            assert normalize_text(
                ITsString(dst.Name.get_String(ws_handle)).Text
            ) == text
