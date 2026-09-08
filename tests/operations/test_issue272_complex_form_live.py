#
#   test_issue272_complex_form_live.py
#
#   Live write-path verification for issue #272: the complex-form write
#   API, which was dead on arrival because both documented entry points
#   resolved their ILexEntryRefFactory through
#   ServiceLocator.GetInstance(...) -- a member ILcmServiceLocator does
#   not declare.
#
#   Covers both entry points named in the issue:
#
#     1. FLExProject.LexiconAddComplexForm(entry, components, type)
#     2. LexEntryOperations.AddComplexFormComponent(complex, component)
#
#   Each test re-queries the owning entry from the LCM after the write
#   (fresh traversal of EntryRefsOS, not the object returned by the
#   call) so the assertion proves the component actually persisted.
#
#   Structure copied from tests/operations/test_target_live_smoke.py:
#   the real Target project, TEST_ prefixes, capture-and-restore in a
#   finally: block.
#
#   Required invocation:
#
#       $env:FLEXLIBS_REQUIRE_LIVE = "1"
#       python -m pytest tests/operations/test_issue272_complex_form_live.py \
#           -m requires_live_project -q
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon import cast_to_concrete

pytestmark = pytest.mark.requires_live_project


TEST_PREFIX = "TEST_"


def _component_forms(project, entry):
    """
    Re-read an entry's complex-form components straight from the LCM.

    Deliberately re-walks EntryRefsOS from the entry rather than
    trusting the ILexEntryRef the write returned -- asserting on the
    returned object would not prove persistence.
    """
    # ServiceLocator.GetObject() is declared to return ICmObject, and
    # ComponentLexemesRS is polymorphic, so both the entry and each
    # component must be downcast before their concrete surface is
    # reachable -- pythonnet only exposes the static type's attributes.
    # This is the #269/#270 mechanism; cast_to_concrete is public per
    # #271. Without these casts the helper itself raises
    # AttributeError: 'ICmObject' object has no attribute 'EntryRefsOS'.
    entry = cast_to_concrete(entry)

    forms = []
    for ref in entry.EntryRefsOS:
        for component in ref.ComponentLexemesRS:
            component = cast_to_concrete(component)
            form = getattr(component, "LexemeFormOA", None)
            text = None
            if form is not None and form.Form is not None:
                text = form.Form.BestVernacularAlternative.Text
            forms.append(text)
    return forms


class TestLexiconAddComplexFormLive:
    """Entry point 1: FLExProject.LexiconAddComplexForm."""

    @pytest.mark.live_phase("FLExProject", "add")
    def test_add_complex_form_persists_components(self, target_project):
        """
        Pre-state: a freshly created complex-form entry has no
        EntryRefsOS components at all.

        Post-state: after LexiconAddComplexForm, a fresh traversal of
        EntryRefsOS from the re-read entry lists both components.

        Pre-fix this raised
        AttributeError: 'ILcmServiceLocator' object has no attribute
        'GetInstance' and the transaction rolled back.
        """
        assert target_project.writeEnabled is True
        entries = target_project.LexEntry

        complex_form = None
        part_a = None
        part_b = None
        try:
            part_a = entries.Create(lexeme_form=f"{TEST_PREFIX}black")
            part_b = entries.Create(lexeme_form=f"{TEST_PREFIX}board")
            complex_form = entries.Create(
                lexeme_form=f"{TEST_PREFIX}blackboard"
            )

            # --- pre-state, read from the LCM ---
            hvo = complex_form.Hvo
            before = _component_forms(target_project, complex_form)
            assert before == [], (
                f"Expected no components before the write, got {before}"
            )

            entry_ref = target_project.LexiconAddComplexForm(
                complex_form, [part_a, part_b], None
            )
            assert entry_ref is not None, (
                "LexiconAddComplexForm returned None"
            )

            # --- post-state, re-queried from the LCM by Hvo ---
            reread = cast_to_concrete(
                target_project.project.ServiceLocator.GetObject(hvo)
            )
            after = _component_forms(target_project, reread)
            assert after == [
                f"{TEST_PREFIX}black",
                f"{TEST_PREFIX}board",
            ], (
                "Components did not persist to the LCM; re-read "
                f"EntryRefsOS gave {after}"
            )
        finally:
            for created in (complex_form, part_a, part_b):
                if created is not None:
                    entries.Delete(created)


class TestAddComplexFormComponentLive:
    """Entry point 2: LexEntryOperations.AddComplexFormComponent."""

    @pytest.mark.live_phase("LexEntryOperations", "add")
    def test_add_complex_form_component_persists(self, target_project):
        """
        Pre-state: the complex-form entry has no components.

        Post-state: after AddComplexFormComponent the re-read entry has
        exactly one component, and it is also registered as the primary
        lexeme (the method's documented first-component behaviour).
        """
        assert target_project.writeEnabled is True
        entries = target_project.LexEntry

        complex_form = None
        component = None
        try:
            component = entries.Create(lexeme_form=f"{TEST_PREFIX}sun")
            complex_form = entries.Create(
                lexeme_form=f"{TEST_PREFIX}sunflower"
            )

            hvo = complex_form.Hvo
            before = _component_forms(target_project, complex_form)
            assert before == [], (
                f"Expected no components before the write, got {before}"
            )

            # AddComplexFormComponent returns None by design; the
            # proof of success is the re-read below.
            entries.AddComplexFormComponent(complex_form, component)

            reread = cast_to_concrete(
                target_project.project.ServiceLocator.GetObject(hvo)
            )
            after = _component_forms(target_project, reread)
            assert after == [f"{TEST_PREFIX}sun"], (
                "Component did not persist to the LCM; re-read "
                f"EntryRefsOS gave {after}"
            )

            primaries = [
                lexeme.Hvo
                for ref in reread.EntryRefsOS
                for lexeme in ref.PrimaryLexemesRS
            ]
            assert component.Hvo in primaries, (
                "First component was not recorded as a primary lexeme; "
                f"PrimaryLexemesRS held {primaries}"
            )
        finally:
            for created in (complex_form, component):
                if created is not None:
                    entries.Delete(created)


class TestAudioPathBuildersLive:
    """
    Cover the third repair in issue #272: SetAudioPath / GetAudioPath
    built their ITsStrBldr and ITsPropsBldr through
    ServiceLocator.GetInstance("TsStrBldr") / ("ITsPropsBldr") -- string
    lookups that could never resolve -- and used the wrong ObjData
    property tag (ord("k") == 107 instead of
    FwTextPropType.ktptObjData == 6).

    Skips cleanly if the Target has no audio writing system configured;
    the builder mechanics themselves are covered offline.
    """

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_audio_path_round_trip(self, target_project):
        assert target_project.writeEnabled is True
        entries = target_project.LexEntry

        # GetAllVernacularWSs returns a set of language-tag strings.
        audio_ws = None
        for tag in sorted(target_project.GetAllVernacularWSs()):
            if "audio" in tag.lower():
                audio_ws = target_project.WSHandle(tag)
                break
        if audio_ws is None:
            pytest.skip(
                "Target has no audio writing system; "
                "SetAudioPath/GetAudioPath cannot be exercised live."
            )

        path = "LinkedFiles/AudioVisual/TEST_issue272.wav"
        created = None
        try:
            created = entries.Create(lexeme_form=f"{TEST_PREFIX}audio")
            form_field = created.LexemeFormOA.Form

            before = target_project.GetAudioPath(form_field, audio_ws)
            assert before is None, (
                f"Expected no audio path before the write, got {before}"
            )

            target_project.SetAudioPath(form_field, audio_ws, path)

            reread = cast_to_concrete(
                target_project.project.ServiceLocator.GetObject(created.Hvo)
            )
            after = target_project.GetAudioPath(
                reread.LexemeFormOA.Form, audio_ws
            )
            assert after == path, (
                f"Audio path did not round-trip: expected {path!r}, "
                f"read back {after!r}"
            )
        finally:
            if created is not None:
                entries.Delete(created)
