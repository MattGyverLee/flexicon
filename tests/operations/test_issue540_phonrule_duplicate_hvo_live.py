#
#   test_issue540_phonrule_duplicate_hvo_live.py
#
#   Live verification for issue #540 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_540_"


def _phon_rule_hvos(project):
    phon_data = project.lp.PhonologicalDataOA
    return [int(rule.Hvo) for rule in phon_data.PhonRulesOS]


class TestIssue540PhonRuleDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("PhonologicalRuleOperations", "write")
    def test_duplicate_insert_after_raw_object_view(self, target_sandbox):
        project = target_sandbox
        phon_ops = project.PhonRules

        rule0 = phon_ops.Create(f"{TEST_PREFIX}a")
        rule1 = phon_ops.Create(f"{TEST_PREFIX}b")
        rule2 = phon_ops.Create(f"{TEST_PREFIX}c")

        raw_mid = project.Object(rule1.Hvo)
        dup = phon_ops.Duplicate(raw_mid, insert_after=True, deep=False)

        order = _phon_rule_hvos(project)
        assert order.index(int(dup.Hvo)) == order.index(int(rule1.Hvo)) + 1

        for rule in list(phon_ops.GetAll()):
            name = phon_ops.GetName(rule)
            if name.startswith(TEST_PREFIX):
                phon_ops.Delete(rule)
