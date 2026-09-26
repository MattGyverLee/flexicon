#
#   test_issue537_morphrule_duplicate_hvo_live.py
#
#   Live verification for issue #537 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_537_"


def _affix_hvos_for_pos(project, pos):
    return [
        int(tmpl.Hvo)
        for tmpl in project.MorphRules.GetAllAffixTemplatesForPOS(pos)
    ]


class TestIssue537MorphRuleDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("MorphRuleOperations", "write")
    def test_duplicate_affix_template_insert_after_raw_object_view(self, target_sandbox):
        project = target_sandbox
        poses = list(project.POS.GetAll())
        assert poses, "Target needs at least one POS for affix-template test"
        pos = poses[0]

        tmpl0 = project.MorphRules.CreateAffixTemplate(
            pos, f"{TEST_PREFIX}a"
        )
        tmpl1 = project.MorphRules.CreateAffixTemplate(
            pos, f"{TEST_PREFIX}b"
        )
        tmpl2 = project.MorphRules.CreateAffixTemplate(
            pos, f"{TEST_PREFIX}c"
        )

        raw_mid = project.Object(tmpl1.Hvo)
        dup = project.MorphRules.Duplicate(raw_mid, insert_after=True, deep=False)

        order = _affix_hvos_for_pos(project, pos)
        assert order.index(int(dup.Hvo)) == order.index(int(tmpl1.Hvo)) + 1

        for tmpl in list(project.MorphRules.GetAllAffixTemplatesForPOS(pos)):
            name = project.MorphRules.GetName(tmpl)
            if name.startswith(TEST_PREFIX):
                project.MorphRules.Delete(tmpl)
