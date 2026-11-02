#
#   test_issue824_wirerule_multi_context_live.py
#
#   Issue #824: WireRule with a multi-element left/right context raised
#   NullReferenceException (MembersRS written on an unowned
#   IPhSequenceContext). Live verification on target_sandbox only.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_824_"


class TestWireRuleMultiElementContext:
    @pytest.mark.live_phase("PhonologicalRule", "write")
    def test_two_element_left_and_right_contexts_in_order(self, target_sandbox):
        from flexicon.code.Shared.rule_patterns import NC
        from flexicon.code.lcm_casting import cast_to_concrete
        from SIL.LCModel import IPhSequenceContext, IPhSimpleContextNC

        proj = target_sandbox
        assert proj.writeEnabled is True
        ncs = proj.NaturalClasses
        nc_a = ncs.Create(f"{TEST_PREFIX}ncA", "A8")
        nc_b = ncs.Create(f"{TEST_PREFIX}ncB", "B8")
        nc_c = ncs.Create(f"{TEST_PREFIX}ncC", "C8")
        nc_d = ncs.Create(f"{TEST_PREFIX}ncD", "D8")
        guids = [nc.Guid for nc in (nc_a, nc_b, nc_c, nc_d)]

        ops = proj.PhonRules
        phon = proj.lp.PhonologicalDataOA
        pool_before = phon.ContextsOS.Count

        rule = ops.Create(f"{TEST_PREFIX}rule")
        ops.WireRule(
            rule,
            input_pattern=[NC(nc_a)],
            output_change=[NC(nc_b)],
            left_context=[NC(nc_a), NC(nc_b)],
            right_context=[NC(nc_c), NC(nc_d)],
        )

        # Re-query everything from the LCM by GUID.
        rule2 = phon.PhonRulesOS[phon.PhonRulesOS.Count - 1]
        assert rule2.Guid == rule.Guid
        rhs = cast_to_concrete(rule2).RightHandSidesOS[0]

        def member_guids(ctx):
            assert ctx is not None
            assert ctx.ClassName == "PhSequenceContext"
            seq = IPhSequenceContext(ctx)
            return [
                IPhSimpleContextNC(m).FeatureStructureRA.Guid
                for m in seq.MembersRS
            ]

        left = member_guids(rhs.LeftContextOA)
        right = member_guids(rhs.RightContextOA)
        print(f"[INFO] pre pool={pool_before} post pool={phon.ContextsOS.Count}")
        print(f"[INFO] left={left} right={right}")
        assert left == [guids[0], guids[1]]
        assert right == [guids[2], guids[3]]
        assert phon.ContextsOS.Count == pool_before + 4
