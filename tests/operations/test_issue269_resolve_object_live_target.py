#
#   test_issue269_resolve_object_live_target.py
#
#   Live verification for issue #269: LexEntryOperations.__ResolveObject
#   never cast, so both of its branches were broken.
#
#   The test file the #269 work shipped
#   (test_lexentry_resolve_object_live.py) depends on the sena3_sandbox
#   fixture, and no "Sena 3*.fwbackup" is present in tests/fixtures, so
#   it cannot run in this checkout. #269's assertions do not actually
#   need pre-existing data: this file creates what it needs on a Target
#   sandbox (a tempdir copy of the Target .fwbackup -- the user's real
#   Target is never touched) so the fix is verified live rather than
#   reported on a skip.
#
#   Both reported defects, plus the rejection that must survive:
#
#     Defect 1 -- the non-int branch returned an uncast object, so a
#       component from the polymorphic ComponentLexemesRS reached
#       GetHeadword's `entry.HeadWord` as an ICmObject and raised
#       AttributeError.
#     Defect 2 -- the HVO branch guarded with isinstance(obj, ILexEntry)
#       against ServiceLocator.GetObject()'s ICmObject-declared return,
#       which is False even for a genuine entry, so a valid entry HVO
#       raised FP_ParameterError.
#     Rejection -- ComponentLexemesRS may legally hold an ILexSense, and
#       a sense's HVO must STILL be refused.
#
#   Required invocation:
#
#       $env:FLEXLIBS_REQUIRE_LIVE = "1"
#       python -m pytest \
#           tests/operations/test_issue269_resolve_object_live_target.py \
#           -m requires_live_project -q
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_269_"


class TestResolveObjectLive:
    """Live proof of both #269 defects against a real LCM."""

    @pytest.mark.live_phase("LexEntryOperations", "read")
    def test_component_from_polymorphic_collection_resolves(
        self, target_sandbox
    ):
        """
        Defect 1. A component handed back by GetComplexFormComponents
        must be usable as an entry.

        Pre-state: the raw element's concrete surface is unreachable on
        its static ICmObject view.
        Post-state: GetHeadword(component), re-read from the LCM,
        returns the headword text that was written.

        Pre-fix this raised
        AttributeError: 'ICmObject' object has no attribute 'HeadWord'.
        """
        entries = target_sandbox.LexEntry
        part = entries.Create(lexeme_form=f"{TEST_PREFIX}stone")
        complex_form = entries.Create(lexeme_form=f"{TEST_PREFIX}milestone")

        target_sandbox.LexiconAddComplexForm(complex_form, [part], None)

        components = entries.GetComplexFormComponents(complex_form)
        assert components, (
            "GetComplexFormComponents returned nothing; the complex form "
            "write did not persist, so this test proves nothing"
        )

        headwords = [entries.GetHeadword(c) for c in components]
        assert any(TEST_PREFIX in str(h) for h in headwords), (
            f"Component headwords did not survive the round trip: "
            f"{headwords}"
        )

    @pytest.mark.live_phase("LexEntryOperations", "read")
    def test_entry_hvo_is_accepted(self, target_sandbox):
        """
        Defect 2. A genuine entry's HVO must resolve.

        Pre-state / post-state: GetHeadword(entry.Hvo) must equal
        GetHeadword(entry), both re-read from the LCM.

        Pre-fix the HVO call raised
        FP_ParameterError: HVO does not refer to a lexical entry.
        """
        entries = target_sandbox.LexEntry
        entry = entries.Create(lexeme_form=f"{TEST_PREFIX}hvo")

        by_object = entries.GetHeadword(entry)
        by_hvo = entries.GetHeadword(entry.Hvo)

        assert by_hvo == by_object, (
            f"HVO resolution disagrees with object resolution: "
            f"{by_hvo!r} != {by_object!r}"
        )
        assert TEST_PREFIX in str(by_object)

    @pytest.mark.live_phase("LexEntryOperations", "read")
    def test_sense_hvo_is_still_rejected(self, target_sandbox):
        """
        The legitimate rejection must survive the widened guard: a
        sense's HVO is not an entry and must still raise.
        """
        entries = target_sandbox.LexEntry
        entry = entries.Create(lexeme_form=f"{TEST_PREFIX}reject")

        senses = list(entry.SensesOS)
        if not senses:
            pytest.skip(
                "Create() produced no blank sense; no sense HVO to test"
            )

        sense_hvo = senses[0].Hvo
        with pytest.raises(FP_ParameterError):
            entries.GetHeadword(sense_hvo)
