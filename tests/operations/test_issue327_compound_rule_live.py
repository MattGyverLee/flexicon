#
#   test_issue327_compound_rule_live.py
#
#   Class: TestIssue327ExoCompoundLive, TestIssue327EndoCompoundLive
#          Live read verification for issue #327 (PR #389): the CompoundRule
#          wrapper's head_last / overriding_msa / to_msa must return the same
#          objects as the raw LCM members, and the removed phantom context
#          properties must stay gone.
#
#   Exo rules are read from sena3_sandbox (Sena 3 carries 4 MoExoCompound
#   rules and no MoEndoCompound). Endo rules are created in
#   target_sandbox, since no sanctioned write project has one.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

_PHANTOM_CONTEXT_PROPS = ("left_context", "right_context", "contexts")


def _same(a, b):
    if a is None or b is None:
        return a is None and b is None
    return a.Guid == b.Guid


class TestIssue327ExoCompoundLive:
    @pytest.mark.live_phase("MorphRuleOperations", "read")
    def test_exo_wrapper_matches_raw_lcm(self, sena3_sandbox):
        from SIL.LCModel import IMoExoCompound

        wrapped = [
            r for r in sena3_sandbox.MorphRules.GetAllCompoundRules()
            if r.is_exo_compound
        ]
        assert wrapped, "Sena 3 should carry MoExoCompound rules"

        seen_to_msa = False
        for rule in wrapped:
            raw = IMoExoCompound(sena3_sandbox.Object(rule.Guid))
            assert _same(rule.to_msa, raw.ToMsaOA)
            seen_to_msa = seen_to_msa or raw.ToMsaOA is not None
            # Endo-only surfaces are gated off on exo rules.
            assert rule.head_last is None
            assert rule.overriding_msa is None
            for name in _PHANTOM_CONTEXT_PROPS:
                assert not hasattr(rule, name)
        assert seen_to_msa, "expected at least one populated ToMsaOA in Sena 3"


class TestIssue327EndoCompoundLive:
    @pytest.mark.live_phase("MorphRuleOperations", "read")
    def test_endo_wrapper_matches_raw_lcm(self, target_sandbox):
        from SIL.LCModel import IMoEndoCompound, IMoStemMsaFactory

        ops = target_sandbox.MorphRules
        created = ops.CreateCompoundRule("TEST_327 endo", endocentric=True)
        raw = IMoEndoCompound(target_sandbox.Object(created.Guid))
        factory = target_sandbox.project.ServiceLocator.GetService(IMoStemMsaFactory)
        with target_sandbox.Transaction("TEST_327 populate endo rule"):
            raw.HeadLast = True
            raw.OverridingMsaOA = factory.Create()

        rule = next(
            r for r in ops.GetAllCompoundRules()
            if r.Guid == raw.Guid
        )
        raw = IMoEndoCompound(target_sandbox.Object(created.Guid))
        assert rule.is_endo_compound
        assert rule.head_last is True
        assert bool(raw.HeadLast) is True
        assert raw.OverridingMsaOA is not None
        assert _same(rule.overriding_msa, raw.OverridingMsaOA)
        assert rule.to_msa is None
        for name in _PHANTOM_CONTEXT_PROPS:
            assert not hasattr(rule, name)
