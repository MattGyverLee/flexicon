#
#   test_issue461_phonological_rule_resolver_cast_live.py
#
#   Live gate for issue #461 PhonologicalRuleOperations HVO resolver cast.
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_461_"


@pytest.mark.requires_live_project
class TestIssue461PhonRuleNameHvoGate:
    """
    GetName resolves the rule via __ResolveObject and reads Name --
    subtype-only on IPhPhonRule.
    """

    @pytest.mark.live_phase("PhonologicalRuleOperations", "read")
    def test_get_name_via_genuine_rule_hvo(self, target_sandbox):
        sandbox = target_sandbox
        rule_name = f"{TEST_PREFIX}Voicing"
        rule = sandbox.PhonRules.Create(rule_name)
        try:
            hvo = rule.Hvo
            assert isinstance(hvo, int), (
                "test setup error: hvo must be a genuine Python int"
            )
            assert not hasattr(sandbox.Object(hvo), "Name"), (
                "precondition failed: Name reachable on bare ICmObject view "
                "-- re-derive the gate site"
            )

            name = sandbox.PhonRules.GetName(hvo)
            assert isinstance(name, str)
            assert TEST_PREFIX in name
        finally:
            sandbox.PhonRules.Delete(rule)
