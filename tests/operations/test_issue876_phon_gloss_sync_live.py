#
#   test_issue876_phon_gloss_sync_live.py
#
#   Issue #876: PhonFeatureOperations GetSyncableProperties gloss fields.
#   Verified on target_sandbox (tempdir copy only).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

TEST_PREFIX = "TEST_876_"


@pytest.mark.requires_live_project
class TestIssue876PhonGlossSyncLive:

    def test_closed_feature_gloss_fields_roundtrip(self, target_sandbox):
        from SIL.LCModel.Core.Text import TsStringUtils
        from SIL.LCModel.Core.KernelInterfaces import ITsString

        p = target_sandbox
        ws_id = next(w.Id for w in p.WritingSystems.GetAll() if w.Handle == p.project.DefaultAnalWs)
        handle = next(w.Handle for w in p.WritingSystems.GetAll() if w.Id == ws_id)

        f1 = p.PhonFeatures.Create(f"{TEST_PREFIX}feat1", f"{TEST_PREFIX}a1")
        f2 = p.PhonFeatures.Create(f"{TEST_PREFIX}feat2", f"{TEST_PREFIX}a2")

        for name, text in (
            ("GlossAbbreviation", f"{TEST_PREFIX}gabbr"),
            ("RightGlossSep", f"{TEST_PREFIX}rsep"),
        ):
            if not hasattr(f1, name):
                pytest.skip(f"IFsClosedFeature has no {name} on this LCM")
            getattr(f1, name).set_String(
                handle, TsStringUtils.MakeString(text, handle)
            )

        if hasattr(f1, "ShowInGloss"):
            f1.ShowInGloss = True

        props = p.PhonFeatures.GetSyncableProperties(f1)
        assert props.get("GlossAbbreviation", {}).get(ws_id) == f"{TEST_PREFIX}gabbr", props
        assert props.get("RightGlossSep", {}).get(ws_id) == f"{TEST_PREFIX}rsep", props
        if "ShowInGloss" in props:
            assert props["ShowInGloss"] is True, props

        p.PhonFeatures.ApplySyncableProperties(f2, props)

        for name, text in (
            ("GlossAbbreviation", f"{TEST_PREFIX}gabbr"),
            ("RightGlossSep", f"{TEST_PREFIX}rsep"),
        ):
            if not hasattr(f2, name):
                continue
            got = ITsString(getattr(f2, name).get_String(handle)).Text
            assert got == text, (name, got)

        if hasattr(f2, "ShowInGloss"):
            assert bool(f2.ShowInGloss) is True
