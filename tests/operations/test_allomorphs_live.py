#
#   test_allomorphs_live.py
#
#   Class: AllomorphOperations
#          Live-DB tests against Sena 3 covering all five phases of the
#          stabilization model:
#              A. read-only
#              B. create + delete in-place (TEST_ prefix, finally cleanup)
#              C. reorder via BaseOperations.MoveUp/MoveDown
#              D. modify (capture-restore)
#              E. delete pre-existing (sandbox copy)
#
#          Allomorphs are owned by ILexEntry via entry.AlternateFormsOS
#          (ordered sequence) -- except for the LexemeFormOA "primary"
#          allomorph which is owned-atomic. AllomorphOperations.Delete
#          uses _GetTypedOwner to cast example.Owner from ICmObject to
#          the concrete ILexEntry so hasattr() reaches the typed
#          collections. This is the fix-pattern that ExampleOperations
#          and PersonOperations lack.
#
#          Test operates exclusively on AlternateFormsOS to avoid
#          touching LexemeFormOA promotion semantics.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import sys

import pytest


pytestmark = pytest.mark.requires_live_project


# ---------------------------------------------------------------------------
# Live-project fixture (canonical pattern)
# ---------------------------------------------------------------------------

_CANDIDATE_PROJECTS = ("Sena 3", "Test", "SampleLexicon", "SampleLexicon3")


def _try_open_project(write_enabled):
    """Open the first candidate project that responds. None if none work."""
    try:
        from flexicon.code.FLExProject import FLExProject
    except Exception:
        return None

    project = FLExProject()
    for name in _CANDIDATE_PROJECTS:
        try:
            project.OpenProject(name, writeEnabled=write_enabled)
            return project
        except Exception:
            continue
    return None


@pytest.fixture(scope="module")
def writable_project():
    """Module-scoped, write-enabled real FLExProject."""
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")

    project = _try_open_project(write_enabled=True)
    if project is None:
        pytest.skip(
            "No writable FieldWorks project available "
            f"(tried: {', '.join(_CANDIDATE_PROJECTS)})"
        )

    yield project

    try:
        project.CloseProject()
    except Exception:
        pass


def _first_entry_with_lexeme_form(project):
    """
    Return the first ILexEntry that already has a LexemeFormOA.

    Create() inherits morph type from entry.LexemeFormOA.MorphTypeRA;
    test entries need that to exist.
    """
    for entry in project.lexDB.Entries:
        if entry.LexemeFormOA and entry.LexemeFormOA.MorphTypeRA:
            return entry
    return None


def _first_entry_with_alternates(project):
    """
    Return the first ILexEntry whose AlternateFormsOS has at least one
    item -- used by Phase E to find a delete target without touching
    LexemeFormOA.
    """
    for entry in project.lexDB.Entries:
        if entry.AlternateFormsOS.Count > 0:
            return entry
    return None


def _delete_test_alternates(project, entry):
    """Pre-clean: remove TEST_-prefixed allomorphs from entry.AlternateFormsOS."""
    for allomorph in list(entry.AlternateFormsOS):
        try:
            form = project.Allomorphs.GetForm(allomorph)
        except Exception:
            continue
        if form and form.startswith("TEST_"):
            try:
                project.Allomorphs.Delete(allomorph)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Phase A: read-only
# ---------------------------------------------------------------------------


class TestAllomorphsPhaseARead:
    """Phase A: getters return without raising."""

    @pytest.mark.live_phase("AllomorphOperations", "read")
    def test_get_all_project_wide(self, writable_project):
        """GetAll() with no argument iterates the whole project."""
        gen = writable_project.Allomorphs.GetAll()
        # AllomorphCollection is iterable; take the first if any.
        try:
            first = next(iter(gen))
            assert first is not None
        except StopIteration:
            pass

    @pytest.mark.live_phase("AllomorphOperations", "read")
    def test_get_all_for_specific_entry(self, writable_project):
        """GetAll(entry) returns a collection for one entry."""
        entry = _first_entry_with_lexeme_form(writable_project)
        if entry is None:
            pytest.skip("Project has no entries with LexemeFormOA")
        collection = writable_project.Allomorphs.GetAll(entry)
        # Should at least contain the LexemeFormOA wrapper.
        items = list(collection)
        assert len(items) >= 1


# ---------------------------------------------------------------------------
# Phase B: create + delete in-place (operates on AlternateFormsOS)
# ---------------------------------------------------------------------------


class TestAllomorphsPhaseBAdd:
    """Phase B: Create + Delete a TEST_ allomorph on an arbitrary entry."""

    @pytest.mark.live_phase("AllomorphOperations", "add")
    def test_create_and_delete_roundtrip(self, writable_project):
        """Create on entry -> verify form -> delete -> verify count restored."""
        entry = _first_entry_with_lexeme_form(writable_project)
        if entry is None:
            pytest.skip("Project has no entries with LexemeFormOA")

        _delete_test_alternates(writable_project, entry)

        form = "TEST_allo_phase_b_roundtrip"
        count_before = entry.AlternateFormsOS.Count
        allomorph = writable_project.Allomorphs.Create(entry, form)
        try:
            assert allomorph is not None
            assert writable_project.Allomorphs.GetForm(allomorph) == form
            assert entry.AlternateFormsOS.Count == count_before + 1
        finally:
            # Surface a Delete failure rather than swallow it.
            writable_project.Allomorphs.Delete(allomorph)

        assert entry.AlternateFormsOS.Count == count_before


# ---------------------------------------------------------------------------
# Phase C: reorder via BaseOperations.MoveUp / MoveDown
# ---------------------------------------------------------------------------


class TestAllomorphsPhaseCReorder:
    """
    Phase C: AllomorphOperations overrides _GetSequence to return
    parent.AlternateFormsOS, so MoveUp / MoveDown work directly.
    """

    @pytest.mark.live_phase("AllomorphOperations", "reorder")
    def test_movedown_then_moveup_restores_order(self, writable_project):
        """Create two alternates, swap them, restore."""
        entry = _first_entry_with_lexeme_form(writable_project)
        if entry is None:
            pytest.skip("Project has no entries with LexemeFormOA")

        _delete_test_alternates(writable_project, entry)

        form_a = "TEST_allo_phase_c_a"
        form_b = "TEST_allo_phase_c_b"

        allo_a = writable_project.Allomorphs.Create(entry, form_a)
        allo_b = writable_project.Allomorphs.Create(entry, form_b)
        try:
            seq = entry.AlternateFormsOS
            idx_a_initial = seq.IndexOf(allo_a)
            idx_b_initial = seq.IndexOf(allo_b)
            assert idx_a_initial >= 0
            assert idx_b_initial >= 0
            assert idx_a_initial < idx_b_initial  # Create appends

            writable_project.Allomorphs.MoveDown(entry, allo_a, positions=1)
            assert seq.IndexOf(allo_a) > seq.IndexOf(allo_b)

            writable_project.Allomorphs.MoveUp(entry, allo_a, positions=1)
            assert seq.IndexOf(allo_a) == idx_a_initial
            assert seq.IndexOf(allo_b) == idx_b_initial
        finally:
            for allo in (allo_a, allo_b):
                try:
                    writable_project.Allomorphs.Delete(allo)
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# Phase D: modify + restore (form text via SetForm)
# ---------------------------------------------------------------------------


class TestAllomorphsPhaseDModify:
    """Phase D: SetForm(new) then SetForm(captured) round-trips."""

    @pytest.mark.live_phase("AllomorphOperations", "modify")
    def test_form_capture_modify_restore(self, writable_project):
        """Capture form, modify, restore."""
        entry = _first_entry_with_lexeme_form(writable_project)
        if entry is None:
            pytest.skip("Project has no entries with LexemeFormOA")

        _delete_test_alternates(writable_project, entry)

        initial = "TEST_allo_phase_d_initial"
        modified = "TEST_allo_phase_d_modified"

        allomorph = writable_project.Allomorphs.Create(entry, initial)
        try:
            captured = writable_project.Allomorphs.GetForm(allomorph)
            assert captured == initial

            writable_project.Allomorphs.SetForm(allomorph, modified)
            assert writable_project.Allomorphs.GetForm(allomorph) == modified

            writable_project.Allomorphs.SetForm(allomorph, captured)
            assert writable_project.Allomorphs.GetForm(allomorph) == initial
        finally:
            try:
                writable_project.Allomorphs.Delete(allomorph)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Phase E: delete pre-existing alternate-form allomorph in sandbox
# ---------------------------------------------------------------------------


class TestAllomorphsPhaseEDelete:
    """
    Phase E: delete a pre-existing alternate-form allomorph inside an
    isolated copy of Sena 3. Skips if no entry has alternates -- some
    lexicons keep almost everything as LexemeFormOA only.
    """

    @pytest.mark.live_phase("AllomorphOperations", "delete")
    def test_delete_preexisting_alternate_in_sandbox(self, sena3_sandbox):
        """Find a pre-existing AlternateFormsOS allomorph, delete it."""
        entry = _first_entry_with_alternates(sena3_sandbox)
        if entry is None:
            pytest.skip(
                "Sandbox project has no entries with AlternateFormsOS items; "
                "cannot exercise Phase E without touching LexemeFormOA"
            )

        count_before = entry.AlternateFormsOS.Count
        assert count_before >= 1

        victim = entry.AlternateFormsOS[0]

        sena3_sandbox.Allomorphs.Delete(victim)

        count_after = entry.AlternateFormsOS.Count
        assert count_after == count_before - 1, (
            f"Expected {count_before - 1} alternates after delete, "
            f"got {count_after}"
        )
