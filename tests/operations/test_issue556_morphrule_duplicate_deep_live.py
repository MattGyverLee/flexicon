#
#   test_issue556_morphrule_duplicate_deep_live.py
#
#   Live verification for issue #556: after the #537 HVO-scan change to
#   MorphRuleOperations.__DuplicateAffixTemplate, the offline mock fixture
#   in test_morphrule_duplicate_deep.py went stale (a bare Mock() is not
#   iterable, so `list(owner.AffixTemplatesOS)` raised TypeError). That was
#   a test-double drift, not a library defect -- this file exercises
#   Duplicate(deep=True/False) against a real LCM-backed affix template
#   with real slots to confirm the library behaviour itself is correct.
#
#   Re-querying uses GetAllAffixTemplatesForPOS(), which returns AffixTemplate
#   wrapper objects with the slots already cast to the concrete interface
#   (.prefix_slots / .suffix_slots / .proclitic_slots / .enclitic_slots).
#   A bare `project.Object(hvo)` deliberately returns an untyped ICmObject
#   (see docs/API_ISSUES_CATEGORIZED.md Category 8 and lcm_casting.py) and
#   has no PrefixSlotsRS et al.; using it here would just re-trigger that
#   documented casting gap in the test's own helper, not in the library
#   under test.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_556_"


def _find_wrapped(project, pos, hvo):
    """Return the AffixTemplate wrapper for hvo from a fresh re-query."""
    for tmpl in project.MorphRules.GetAllAffixTemplatesForPOS(pos):
        if int(tmpl.Hvo) == hvo:
            return tmpl
    return None


def _slot_hvo_lists(wrapped_template):
    """(Prefix, Suffix, Proclitic, Enclitic) slot HVO lists for a wrapped template."""
    return (
        [int(s.Hvo) for s in wrapped_template.prefix_slots],
        [int(s.Hvo) for s in wrapped_template.suffix_slots],
        [int(s.Hvo) for s in wrapped_template.proclitic_slots],
        [int(s.Hvo) for s in wrapped_template.enclitic_slots],
    )


def _affix_hvos_for_pos(project, pos):
    return [
        int(tmpl.Hvo)
        for tmpl in project.MorphRules.GetAllAffixTemplatesForPOS(pos)
    ]


class TestIssue556MorphRuleDuplicateDeepLive:
    """Duplicate(deep=True/False) on an affix template with real slots."""

    @pytest.mark.live_phase("MorphRuleOperations", "write")
    def test_deep_true_copies_slot_references(self, sena3_sandbox):
        project = sena3_sandbox
        poses = list(project.POS.GetAll())
        assert poses, "Sena 3 sandbox needs at least one POS"
        pos = poses[0]

        prefix_slot = project.POS.CreateAffixSlot(pos, f"{TEST_PREFIX}pfx")
        suffix_slot = project.POS.CreateAffixSlot(pos, f"{TEST_PREFIX}sfx")

        source = project.MorphRules.CreateAffixTemplate(pos, f"{TEST_PREFIX}src_deep")
        project.MorphRules.AddSlotToTemplate(source, prefix_slot, "prefix")
        project.MorphRules.AddSlotToTemplate(source, suffix_slot, "suffix")

        # Pre-state, read back from the LCM via a fresh re-query.
        source_hvo = int(source.Hvo)
        pre_order = _affix_hvos_for_pos(project, pos)
        source_index = pre_order.index(source_hvo)
        pre_count = len(pre_order)
        pre_prefix, pre_suffix, pre_proclitic, pre_enclitic = _slot_hvo_lists(
            _find_wrapped(project, pos, source_hvo)
        )
        assert pre_prefix and pre_suffix, "Fixture setup did not attach slots"

        try:
            duplicate = project.MorphRules.Duplicate(source, insert_after=True, deep=True)
            dup_hvo = int(duplicate.Hvo)

            # Re-query from the LCM -- never assert on the value just passed in.
            post_order = _affix_hvos_for_pos(project, pos)
            requeried_dup = _find_wrapped(project, pos, dup_hvo)
            assert requeried_dup is not None, "Duplicate not found on re-query"
            dup_prefix, dup_suffix, dup_proclitic, dup_enclitic = _slot_hvo_lists(
                requeried_dup
            )

            assert dup_prefix == pre_prefix
            assert dup_suffix == pre_suffix
            assert dup_proclitic == pre_proclitic == []
            assert dup_enclitic == pre_enclitic == []
            assert post_order.index(dup_hvo) == source_index + 1
            assert len(post_order) == pre_count + 1
        finally:
            for tmpl in list(project.MorphRules.GetAllAffixTemplatesForPOS(pos)):
                name = project.MorphRules.GetName(tmpl)
                if name.startswith(TEST_PREFIX):
                    project.MorphRules.Delete(tmpl)

    @pytest.mark.live_phase("MorphRuleOperations", "write")
    def test_deep_false_does_not_copy_slot_references(self, sena3_sandbox):
        project = sena3_sandbox
        poses = list(project.POS.GetAll())
        assert poses, "Sena 3 sandbox needs at least one POS"
        pos = poses[0]

        prefix_slot = project.POS.CreateAffixSlot(pos, f"{TEST_PREFIX}pfx2")

        source = project.MorphRules.CreateAffixTemplate(pos, f"{TEST_PREFIX}src_shallow")
        project.MorphRules.AddSlotToTemplate(source, prefix_slot, "prefix")

        source_hvo = int(source.Hvo)
        pre_order = _affix_hvos_for_pos(project, pos)
        source_index = pre_order.index(source_hvo)
        pre_count = len(pre_order)
        pre_prefix, pre_suffix, pre_proclitic, pre_enclitic = _slot_hvo_lists(
            _find_wrapped(project, pos, source_hvo)
        )
        assert pre_prefix, "Fixture setup did not attach a prefix slot"

        try:
            duplicate = project.MorphRules.Duplicate(source, insert_after=True, deep=False)
            dup_hvo = int(duplicate.Hvo)

            post_order = _affix_hvos_for_pos(project, pos)
            requeried_dup = _find_wrapped(project, pos, dup_hvo)
            assert requeried_dup is not None, "Duplicate not found on re-query"
            dup_prefix, dup_suffix, dup_proclitic, dup_enclitic = _slot_hvo_lists(
                requeried_dup
            )

            # Duplicate's own slot lists must be empty -- deep=False must not copy.
            assert dup_prefix == []
            assert dup_suffix == []
            assert dup_proclitic == []
            assert dup_enclitic == []

            # Source itself must be unchanged.
            requeried_source = _find_wrapped(project, pos, source_hvo)
            post_source_prefix, post_source_suffix, _, _ = _slot_hvo_lists(
                requeried_source
            )
            assert post_source_prefix == pre_prefix
            assert post_source_suffix == pre_suffix == []

            assert post_order.index(dup_hvo) == source_index + 1
            assert len(post_order) == pre_count + 1
        finally:
            for tmpl in list(project.MorphRules.GetAllAffixTemplatesForPOS(pos)):
                name = project.MorphRules.GetName(tmpl)
                if name.startswith(TEST_PREFIX):
                    project.MorphRules.Delete(tmpl)
