#
#   test_lexentry_resolve_object_live.py
#
#   Class: TestLexEntryResolveObjectLive
#          Live verification for issue #269. Modelled on
#          tests/operations/test_target_live_smoke.py.
#
#          The two defects can only be proven against a real LCM,
#          because both are pythonnet static-type artefacts:
#            1. An entry reached through a polymorphic collection is
#               typed ICmObject, so entry.HeadWord raised
#               AttributeError before __ResolveObject cast it.
#            2. FLExProject.Object(hvo) -> ServiceLocator.GetObject()
#               is declared to return ICmObject, so the old
#               isinstance(obj, ILexEntry) guard rejected genuine
#               entries with "HVO does not refer to a lexical entry".
#
#          Read-path only: nothing here writes, so it runs against the
#          populated Sena 3 sandbox.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project


def _find_complex_form_with_components(project):
    """Return (complex_entry, components) for the first complex form."""
    entries = project.LexEntry
    for entry in entries.GetAll():
        try:
            components = list(entries.GetComplexFormComponents(entry))
        except Exception:
            continue
        if components:
            return entry, components
    return None, []


class TestLexEntryResolveObjectLive:
    """Both #269 defects, against a live LCM."""

    @pytest.mark.live_phase("LexEntryOperations", "read")
    def test_component_from_polymorphic_collection_yields_headword(
        self, sena3_sandbox
    ):
        """
        Defect 1: a component reached via GetComplexFormComponents
        arrives typed ICmObject. GetHeadword must return a real
        headword string instead of raising
        AttributeError: 'ICmObject' object has no attribute 'HeadWord'.
        """
        entries = sena3_sandbox.LexEntry
        complex_entry, components = _find_complex_form_with_components(
            sena3_sandbox
        )
        if complex_entry is None:
            pytest.fail(
                "No complex form with components found in Sena 3 -- "
                "cannot verify #269 defect 1 on this project."
            )

        entry_components = [
            c for c in components
            if getattr(c, "ClassName", None) == "LexEntry"
        ]
        if not entry_components:
            pytest.fail(
                "Complex form components contained no LexEntry -- "
                "cannot verify #269 defect 1 on this project."
            )

        for component in entry_components:
            # Pre-state: the raw component has no HeadWord on its
            # static ICmObject view.
            pre_has_headword = hasattr(component, "HeadWord")

            headword = entries.GetHeadword(component)

            assert isinstance(headword, str) and headword != "", (
                f"GetHeadword returned {headword!r} for component "
                f"hvo={component.Hvo} (pre-cast hasattr(HeadWord)="
                f"{pre_has_headword})"
            )

    @pytest.mark.live_phase("LexEntryOperations", "read")
    def test_entry_hvo_is_accepted_and_matches_object_path(
        self, sena3_sandbox
    ):
        """
        Defect 2: GetHeadword(entry.Hvo) must succeed and agree with
        GetHeadword(entry). This is the exact production failure --
        code that had already established ClassName == "LexEntry" was
        still refused with FP_ParameterError.
        """
        entries = sena3_sandbox.LexEntry
        sampled = 0
        for entry in entries.GetAll():
            by_object = entries.GetHeadword(entry)
            by_hvo = entries.GetHeadword(entry.Hvo)
            assert by_hvo == by_object, (
                f"HVO path disagreed with object path for hvo="
                f"{entry.Hvo}: {by_hvo!r} != {by_object!r}"
            )
            sampled += 1
            if sampled >= 25:
                break

        assert sampled > 0, "Sena 3 yielded no entries to sample."

    @pytest.mark.live_phase("LexEntryOperations", "read")
    def test_sense_hvo_is_still_rejected(self, sena3_sandbox):
        """
        The legitimate rejection must survive the fix: a sense's HVO is
        not a lexical entry and must still raise FP_ParameterError.
        """
        from flexicon.code.FLExProject import FP_ParameterError

        entries = sena3_sandbox.LexEntry
        sense_hvo = None
        for entry in entries.GetAll():
            senses = list(entry.SensesOS)
            if senses:
                sense_hvo = senses[0].Hvo
                break

        if sense_hvo is None:
            pytest.fail("No sense found in Sena 3 to test rejection with.")

        with pytest.raises(FP_ParameterError) as excinfo:
            entries.GetHeadword(sense_hvo)

        assert "does not refer to a lexical entry" in str(excinfo.value)
