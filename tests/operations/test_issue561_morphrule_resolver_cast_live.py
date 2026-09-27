#
#   test_issue561_morphrule_resolver_cast_live.py
#
#   Live write-path verification for issue #561 against target_sandbox.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#
#   Issue #561: MorphRuleOperations.__ResolveObject only cast a bare
#   ICmObject when ClassName == "PartOfSpeech", so an affix template or
#   compound rule reached by HVO stayed an uncast ICmObject and every
#   concrete-only member (Name, PrefixSlotsRS, HeadLast, ...) raised
#   AttributeError.
#
#   The defect is in the RESOLVER, not in the callers, so every test here
#   passes the HVO (and the raw project.Object(hvo)) -- the documented
#   input shape that always failed. Passing a typed object from GetAll()
#   would exercise the pre-cast path and prove nothing.
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_561_"


def _template_still_on_pos(project, pos_hvo, template_hvo):
    """Re-query the LCM for template_hvo among pos_hvo's templates."""
    from SIL.LCModel import IMoInflAffixTemplate, IPartOfSpeech

    owner = IPartOfSpeech(project.Object(pos_hvo))
    for raw in owner.AffixTemplatesOS:
        if raw.Hvo == template_hvo:
            return IMoInflAffixTemplate(raw)
    return None


def _compound_rule_by_hvo(project, rule_hvo):
    """Re-query the LCM for rule_hvo among MoMorphData.CompoundRulesOS."""
    for raw in project.lp.MorphologicalDataOA.CompoundRulesOS:
        if raw.Hvo == rule_hvo:
            return raw
    return None


class TestIssue561MorphRuleResolverCastLive:
    """MorphRuleOperations resolves all four ClassNames, not just POS."""

    @pytest.mark.live_phase("MorphRuleOperations", "add")
    def test_duplicate_affix_template_by_hvo_casts_template(self, target_sandbox):
        """HVO input yields a typed IMoInflAffixTemplate, not a bare ICmObject."""
        project = target_sandbox
        assert project.writeEnabled is True

        poses = list(project.POS.GetAll())
        assert poses, "Target needs at least one POS for affix-template test"
        pos = poses[0]
        pos_hvo = int(pos.Hvo)

        before = len(list(project.MorphRules.GetAllAffixTemplatesForPOS(pos)))

        source = project.MorphRules.CreateAffixTemplate(
            pos, f"{TEST_PREFIX}by_hvo"
        )
        source_hvo = int(source.Hvo)
        try:
            # The defect: this raised
            # AttributeError: 'ICmObject' object has no attribute 'Name'
            duplicate = project.MorphRules.Duplicate(source_hvo, insert_after=True)
            assert duplicate is not None
            assert int(duplicate.Hvo) != source_hvo

            # Read back from the LCM rather than trusting the return value.
            landed = _template_still_on_pos(project, pos_hvo, int(duplicate.Hvo))
            assert landed is not None, "duplicate not present on POS in the LCM"

            # Name only resolves if the cast happened; and it must equal the
            # source's name, which Duplicate copies via CopyAlternatives.
            assert project.MorphRules.GetName(int(duplicate.Hvo)) == (
                f"{TEST_PREFIX}by_hvo"
            )

            after = len(list(project.MorphRules.GetAllAffixTemplatesForPOS(pos)))
            assert after == before + 2
        finally:
            for tmpl in list(project.MorphRules.GetAllAffixTemplatesForPOS(pos)):
                if project.MorphRules.GetName(tmpl).startswith(TEST_PREFIX):
                    project.MorphRules.Delete(tmpl)

    @pytest.mark.live_phase("MorphRuleOperations", "add")
    def test_duplicate_affix_template_by_raw_object_casts_template(
        self, target_sandbox
    ):
        """A raw ICmObject from project.Object(hvo) is cast too."""
        project = target_sandbox
        assert project.writeEnabled is True

        poses = list(project.POS.GetAll())
        assert poses, "Target needs at least one POS for affix-template test"
        pos = poses[0]
        pos_hvo = int(pos.Hvo)

        source = project.MorphRules.CreateAffixTemplate(
            pos, f"{TEST_PREFIX}raw_object"
        )
        source_hvo = int(source.Hvo)
        try:
            # project.Object() is declared to return ICmObject, so this is
            # the exact object the resolver used to hand back uncast.
            duplicate = project.MorphRules.Duplicate(
                project.Object(source_hvo), insert_after=True
            )
            assert duplicate is not None
            assert int(duplicate.Hvo) != source_hvo
            assert _template_still_on_pos(project, pos_hvo, int(duplicate.Hvo)) is not None
        finally:
            for tmpl in list(project.MorphRules.GetAllAffixTemplatesForPOS(pos)):
                if project.MorphRules.GetName(tmpl).startswith(TEST_PREFIX):
                    project.MorphRules.Delete(tmpl)

    @pytest.mark.live_phase("MorphRuleOperations", "add")
    def test_duplicate_compound_rule_by_hvo_casts_rule(self, target_sandbox):
        """MoEndoCompound/MoExoCompound also arrive cast, not as bare ICmObject."""
        project = target_sandbox
        assert project.writeEnabled is True

        rule = project.MorphRules.CreateCompoundRule(
            f"{TEST_PREFIX}compound", endocentric=True
        )
        rule_hvo = int(rule.Hvo)
        before = len(list(project.MorphRules.GetAllCompoundRules()))
        try:
            duplicate = project.MorphRules.Duplicate(rule_hvo, insert_after=True)
            assert duplicate is not None
            assert int(duplicate.Hvo) != rule_hvo

            assert _compound_rule_by_hvo(project, int(duplicate.Hvo)) is not None
            # Name is a concrete-only member on IMoCompoundRule.
            assert project.MorphRules.GetName(rule_hvo) == f"{TEST_PREFIX}compound"
            assert project.MorphRules.GetName(int(duplicate.Hvo)) == (
                f"{TEST_PREFIX}compound"
            )

            after = len(list(project.MorphRules.GetAllCompoundRules()))
            assert after == before + 1
        finally:
            for item in list(project.MorphRules.GetAllCompoundRules()):
                if project.MorphRules.GetName(item).startswith(TEST_PREFIX):
                    project.MorphRules.Delete(item)

    @pytest.mark.live_phase("MorphRuleOperations", "add")
    def test_part_of_speech_hvo_still_casts(self, target_sandbox):
        """The pre-existing PartOfSpeech cast is preserved, not regressed.

        AddSlotToTemplate depends on it: it reads AllAffixSlots, which is
        only reachable on IPartOfSpeech.
        """
        project = target_sandbox
        assert project.writeEnabled is True

        poses = list(project.POS.GetAll())
        assert poses, "Target needs at least one POS for affix-template test"
        pos = poses[0]
        pos_hvo = int(pos.Hvo)

        templates = project.MorphRules.GetAllAffixTemplatesForPOS(pos_hvo)
        assert templates is not None
