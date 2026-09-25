#
#   test_issue467_morphrule_owner_cast_live.py
#
#   Live write-path verification for issue #467 against target_sandbox.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_467_"


def _template_still_on_pos(project, pos_hvo, template_hvo):
    from SIL.LCModel import IMoInflAffixTemplate, IPartOfSpeech

    owner = IPartOfSpeech(project.Object(pos_hvo))
    for raw in owner.AffixTemplatesOS:
        if raw.Hvo == template_hvo:
            return IMoInflAffixTemplate(raw)
    return None


class TestIssue467MorphRuleOwnerCastLive:
    """Delete and Duplicate affix templates via typed POS owner."""

    @pytest.mark.live_phase("MorphRuleOperations", "add")
    def test_delete_affix_template_removes_from_pos(self, target_sandbox):
        project = target_sandbox
        assert project.writeEnabled is True

        poses = list(project.POS.GetAll())
        assert poses, "Target needs at least one POS for affix-template test"
        pos = poses[0]
        pos_hvo = int(pos.Hvo)

        template = project.MorphRules.CreateAffixTemplate(
            pos, f"{TEST_PREFIX}delete_me"
        )
        template_hvo = int(template.Hvo)
        assert _template_still_on_pos(project, pos_hvo, template_hvo) is not None

        project.MorphRules.Delete(template)
        assert _template_still_on_pos(project, pos_hvo, template_hvo) is None

    @pytest.mark.live_phase("MorphRuleOperations", "add")
    def test_duplicate_affix_template_inserts_on_pos(self, target_sandbox):
        project = target_sandbox
        assert project.writeEnabled is True

        poses = list(project.POS.GetAll())
        assert poses, "Target needs at least one POS for affix-template test"
        pos = poses[0]
        pos_hvo = int(pos.Hvo)

        before = len(list(project.MorphRules.GetAllAffixTemplatesForPOS(pos)))

        source = project.MorphRules.CreateAffixTemplate(
            pos, f"{TEST_PREFIX}dup_source"
        )
        try:
            after_create = len(
                list(project.MorphRules.GetAllAffixTemplatesForPOS(pos))
            )
            assert after_create == before + 1

            duplicate = project.MorphRules.Duplicate(source, insert_after=True)
            assert duplicate is not None
            assert int(duplicate.Hvo) != int(source.Hvo)

            after_dup = len(list(project.MorphRules.GetAllAffixTemplatesForPOS(pos)))
            assert after_dup == before + 2
            assert _template_still_on_pos(project, pos_hvo, int(duplicate.Hvo)) is not None
        finally:
            for tmpl in list(project.MorphRules.GetAllAffixTemplatesForPOS(pos)):
                name = project.MorphRules.GetName(tmpl)
                if name.startswith(TEST_PREFIX):
                    project.MorphRules.Delete(tmpl)
