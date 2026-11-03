#
#   test_issue886_variant_lexemeform_sync_live.py
#
#   Issue #886: VariantOperations sync must round-trip owning-entry LexemeForm.
#   Verified on target_sandbox (tempdir copy only).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

TEST_PREFIX = "TEST_"
SRC_WS = "zz-src"


def _vernacular(project):
    ws = project.project.VernacularWs
    for w in project.WritingSystems.GetAll():
        if w.Handle == ws:
            return w.Id, ws
    raise AssertionError("no vernacular WS")


@pytest.mark.requires_live_project
class TestIssue886Live:

    def test_variant_ref_lexeme_form_roundtrip(self, target_sandbox):
        from SIL.LCModel.Core.KernelInterfaces import ITsString

        p = target_sandbox
        ws_id, handle = _vernacular(p)
        vtype = next(iter(p.Variants.GetAllTypes()), None)
        if vtype is None:
            pytest.skip("Target has no variant types")

        e1 = p.LexEntry.Create(f"{TEST_PREFIX}e886a")
        ref1 = p.Variants.Create(e1, f"{TEST_PREFIX}formA", vtype)
        e2 = p.LexEntry.Create(f"{TEST_PREFIX}e886b")
        ref2 = p.Variants.Create(e2, f"{TEST_PREFIX}placeholder", vtype)

        props = p.Variants.GetSyncableProperties(ref1)
        assert props.get("LexemeForm", {}).get(ws_id) == f"{TEST_PREFIX}formA", props

        mapped = dict(props)
        mapped["LexemeForm"] = {SRC_WS: props["LexemeForm"][ws_id]}
        p.Variants.ApplySyncableProperties(
            ref2, mapped, ws_map={SRC_WS: ws_id}
        )
        got = ITsString(e2.LexemeFormOA.Form.get_String(handle)).Text
        assert got == f"{TEST_PREFIX}formA", got
