#
#   test_issue878_infltype_gloss_sync_live.py
#
#   Issue #878: VariantOperations LexEntryInflType gloss sync fields.
#   Verified on target_sandbox (tempdir copy only).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

TEST_PREFIX = "TEST_878_"
SRC_WS = "zz-src"


def _infl_types(project):
    from flexicon.code.lcm_casting import cast_to_concrete

    found = []
    for raw in project.Variants.GetAllTypes():
        t = cast_to_concrete(raw)
        if getattr(t, "ClassName", None) == "LexEntryInflType":
            found.append(t)
    return found


def _analysis(project):
    handle = project.project.DefaultAnalWs
    for ws in project.WritingSystems.GetAll():
        if ws.Handle == handle:
            return ws.Id, handle
    raise AssertionError("no default analysis WS")


@pytest.mark.requires_live_project
class TestIssue878InflTypeGlossSyncLive:

    def test_lex_entry_infl_type_gloss_roundtrip(self, target_sandbox):
        from SIL.LCModel.Core.Text import TsStringUtils
        from SIL.LCModel.Core.KernelInterfaces import ITsString

        p = target_sandbox
        types = _infl_types(p)
        if len(types) < 2:
            pytest.skip("need two LexEntryInflType rows in VariantEntryTypesOA")
        src, dst = types[0], types[1]
        ws_id, handle = _analysis(p)

        for name, val in (("GlossPrepend", "["), ("GlossAppend", "]")):
            prop = getattr(src, name)
            prop.set_String(handle, TsStringUtils.MakeString(f"{TEST_PREFIX}{name}", handle))

        props = p.Variants.GetTypeSyncableProperties(src)
        assert props.get("GlossPrepend") == {ws_id: f"{TEST_PREFIX}GlossPrepend"}, props
        assert props.get("GlossAppend") == {ws_id: f"{TEST_PREFIX}GlossAppend"}, props

        props2 = {
            "GlossPrepend": {SRC_WS: props["GlossPrepend"][ws_id]},
            "GlossAppend": {SRC_WS: props["GlossAppend"][ws_id]},
        }
        p.Variants.ApplyTypeSyncableProperties(
            dst, props2, ws_map={SRC_WS: ws_id}
        )

        for name in ("GlossPrepend", "GlossAppend"):
            got = ITsString(getattr(dst, name).get_String(handle)).Text
            assert got == f"{TEST_PREFIX}{name}", got
