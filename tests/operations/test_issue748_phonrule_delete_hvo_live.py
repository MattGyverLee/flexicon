#
#   test_issue748_phonrule_delete_hvo_live.py
#
#   Live verification for issue #748 PhonRulesOS / FeatConstraintsOS HVO lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_748_"


@pytest.mark.requires_live_project
class TestIssue748PhonRuleDeleteHvoLive:
    """Delete must not rely on Python proxy identity in PhonRulesOS."""

    def test_delete_rule_via_resolved_hvo(self, target_project):
        project = target_project
        name = TEST_PREFIX + "rule"
        rule = project.PhonRules.Create(name)
        hvo = int(rule.Hvo)
        resolved = project.Object(hvo)
        project.PhonRules.Delete(resolved)
        assert project.PhonRules.Find(name) is None
