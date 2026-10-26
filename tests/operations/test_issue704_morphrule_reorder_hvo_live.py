#
#   test_issue704_morphrule_reorder_hvo_live.py
#
#   Live verification for issue #704 ReorderAffixTemplates HVO membership partition.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_704_"


def _affix_hvos_for_pos(project, pos):
    return [
        int(tmpl.Hvo)
        for tmpl in project.MorphRules.GetAllAffixTemplatesForPOS(pos)
    ]


class TestIssue704MorphRuleReorderHvoLive:
    """ReorderAffixTemplates must accept project.Object(hvo) handles."""

    @pytest.mark.live_phase("MorphRuleOperations", "write")
    def test_reorder_affix_templates_accepts_object_hvo_views(self, target_sandbox):
        project = target_sandbox
        poses = list(project.POS.GetAll())
        assert poses, "Target needs at least one POS for affix-template test"
        pos = poses[0]

        tmpl0 = project.MorphRules.CreateAffixTemplate(pos, f"{TEST_PREFIX}a")
        tmpl1 = project.MorphRules.CreateAffixTemplate(pos, f"{TEST_PREFIX}b")
        tmpl2 = project.MorphRules.CreateAffixTemplate(pos, f"{TEST_PREFIX}c")

        try:
            handles = [
                project.Object(tmpl2.Hvo),
                project.Object(tmpl0.Hvo),
                project.Object(tmpl1.Hvo),
            ]
            project.MorphRules.ReorderAffixTemplates(pos, handles)

            order = _affix_hvos_for_pos(project, pos)
            test_order = [
                int(tmpl2.Hvo),
                int(tmpl0.Hvo),
                int(tmpl1.Hvo),
            ]
            assert [h for h in order if h in test_order] == test_order
        finally:
            for tmpl in list(project.MorphRules.GetAllAffixTemplatesForPOS(pos)):
                name = project.MorphRules.GetName(tmpl)
                if name.startswith(TEST_PREFIX):
                    project.MorphRules.Delete(tmpl)
