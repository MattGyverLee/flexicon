#
#   test_issue802_morphrule_delete_hvo_live.py
#
#   Live gate for issue #802 Delete HVO membership on CompoundRulesOS.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_802_"


@pytest.mark.requires_live_project
class TestIssue802MorphRuleDeleteHvoLive:
    """Delete must remove the compound rule when passed Object(hvo)."""

    @pytest.mark.live_phase("MorphRuleOperations", "delete")
    def test_delete_compound_rule_via_resolved_hvo(self, target_sandbox):
        rule_ops = target_sandbox.MorphRules
        name = f"{TEST_PREFIX}compound"

        rule = None
        try:
            rule = rule_ops.CreateCompoundRule(name)
            assert rule is not None
            rule_hvo = int(rule.Hvo)

            before = len(list(rule_ops.GetAllCompoundRules()))
            resolved = target_sandbox.Object(rule_hvo)
            rule_ops.Delete(resolved)

            assert len(list(rule_ops.GetAllCompoundRules())) == before - 1
            for remaining in rule_ops.GetAllCompoundRules():
                assert int(remaining.Hvo) != rule_hvo
            rule = None
        finally:
            if rule is not None:
                try:
                    rule_ops.Delete(rule)
                except Exception:
                    pass
