#
#   test_issue872_metathesis_strucchange_sync_live.py
#
#   Issue #872: PhMetathesisRule.StrucChange round-trips through
#   GetSyncableProperties / ApplySyncableProperties. Verified on target_sandbox.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon.code.lcm_casting import _get_factory_for_class

TEST_PREFIX = "TEST_"


@pytest.mark.requires_live_project
class TestIssue872Live:
    def test_metathesis_strucchange_roundtrip(self, target_sandbox):
        from SIL.LCModel.Core.KernelInterfaces import ITsString
        from SIL.LCModel.Core.Text import TsStringUtils

        p = target_sandbox
        assert p.writeEnabled is True
        phon = p.lp.PhonologicalDataOA
        assert phon is not None, "Target has no PhonologicalDataOA"

        ops = p.PhonRules
        handle = p.project.DefaultAnalWs
        factory = _get_factory_for_class("PhMetathesisRule", p.project)
        assert factory is not None, "PhMetathesisRule factory missing on this LCM"

        r1 = r2 = None
        try:
            with ops._TransactionCM("TEST_872 seed metathesis rules"):
                r1 = factory.Create()
                r2 = factory.Create()
                phon.PhonRulesOS.Add(r1)
                phon.PhonRulesOS.Add(r2)

            val = f"{TEST_PREFIX}struc872"
            r1.StrucChange = TsStringUtils.MakeString(val, handle)

            props = ops.GetSyncableProperties(r1)
            assert props.get("StrucChange") == val, props

            assert ITsString(r2.StrucChange).Text in (None, "")
            ops.ApplySyncableProperties(r2, {"StrucChange": props["StrucChange"]})
            assert ITsString(r2.StrucChange).Text == val
        finally:
            try:
                with ops._TransactionCM("TEST_872 cleanup metathesis rules"):
                    for rule in (r1, r2):
                        if rule is not None and rule in phon.PhonRulesOS:
                            phon.PhonRulesOS.Remove(rule)
            except Exception:
                pass
