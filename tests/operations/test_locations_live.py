#
#   test_locations_live.py
#
#   Class: LocationOperations
#          Live-DB tests against Sena 3 covering all five phases of the
#          stabilization model:
#              A. read-only
#              B. create + delete in-place (TEST_ prefix, finally cleanup)
#              C. reorder (capture-restore)
#              D. modify (capture-restore)
#              E. delete in sandbox copy
#
#          Sena 3 ships with zero existing locations, which makes
#          LocationOperations the cleanest template -- Phases B-D have
#          no risk of collision with pre-existing data. Phase E uses
#          the shared sena3_sandbox fixture so destructive operations
#          never touch the user's real Sena 3.
#
#          This file is the canonical Cycle-2 template; replicate its
#          structure to test_persons_live.py, test_notes_live.py, etc.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import sys

import pytest


# Every test in this module opens a real .fwdata project via writable_project
# or sena3_sandbox.
pytestmark = pytest.mark.requires_live_project


# ---------------------------------------------------------------------------
# Live-project fixture (matches the canonical pattern from test_phonemes.py)
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
    """
    Module-scoped, write-enabled real FLExProject. Skipped if SIL.LCModel
    isn't loaded or no candidate project opens.
    """
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


def _delete_if_present(project, name):
    """Pre-clean a TEST_ location left from a crashed prior run."""
    existing = project.Location.Find(name)
    if existing is not None:
        try:
            project.Location.Delete(existing)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Phase A: read-only
# ---------------------------------------------------------------------------


class TestLocationsPhaseARead:
    """Phase A: getters return without raising, regardless of count."""

    @pytest.mark.live_phase("LocationOperations", "read")
    def test_get_all_returns_list(self, writable_project):
        """GetAll() returns a list (possibly empty) without raising."""
        locations = writable_project.Location.GetAll()
        assert isinstance(locations, list)

    @pytest.mark.live_phase("LocationOperations", "read")
    def test_find_returns_none_for_missing(self, writable_project):
        """Find() returns None for a name that cannot exist."""
        result = writable_project.Location.Find(
            "TEST_zzqxxx_nonexistent_for_phase_a"
        )
        assert result is None

    @pytest.mark.live_phase("LocationOperations", "read")
    def test_exists_returns_false_for_missing(self, writable_project):
        """Exists() returns False for a name that cannot exist."""
        assert (
            writable_project.Location.Exists(
                "TEST_zzqxxx_nonexistent_for_phase_a"
            )
            is False
        )


# ---------------------------------------------------------------------------
# Phase B: create + delete in-place (TEST_ prefix, finally cleanup)
# ---------------------------------------------------------------------------


class TestLocationsPhaseBAdd:
    """Phase B: create a TEST_ location, verify, delete in finally."""

    @pytest.mark.live_phase("LocationOperations", "add")
    def test_create_and_delete_roundtrip(self, writable_project):
        """Create -> assert name + Exists -> Delete -> assert absent."""
        name = "TEST_loc_phase_b_roundtrip"

        _delete_if_present(writable_project, name)

        location = writable_project.Location.Create(name)
        try:
            assert location is not None
            assert writable_project.Location.GetName(location) == name
            assert writable_project.Location.Exists(name) is True
        finally:
            try:
                writable_project.Location.Delete(location)
            except Exception:
                pass

        assert writable_project.Location.Find(name) is None

    @pytest.mark.live_phase("LocationOperations", "add")
    def test_create_with_alias(self, writable_project):
        """Create with alias -> verify both name and alias round-trip."""
        name = "TEST_loc_phase_b_alias"
        alias = "TBA"

        _delete_if_present(writable_project, name)

        location = writable_project.Location.Create(name, alias=alias)
        try:
            assert writable_project.Location.GetName(location) == name
            assert writable_project.Location.GetAlias(location) == alias
        finally:
            try:
                writable_project.Location.Delete(location)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Phase C: reorder (capture-restore)
# ---------------------------------------------------------------------------


class TestLocationsPhaseCReorder:
    """
    Phase C: capture original order, perform a swap, restore.

    Important LCM semantic: `LcmOwningSequence.Remove(item)` does NOT
    just unlink the item from the sequence -- it DELETES the owned
    object outright (orphan deletion). A naive Remove+Insert reorder
    pattern raises `LcmObjectDeletedException` on the second call.

    The LCM-correct API for in-sequence reordering is:
        sequence.MoveTo(srcStart, srcEnd, destSeq, destIndex)
    which moves a slice without deleting the objects. BaseOperations
    wraps this in MoveUp/MoveDown/MoveToIndex helpers, but those
    require subclasses to override `_GetSequence(parent)` -- which
    LocationOperations does not. The test below calls MoveTo directly
    on the OS list.
    """

    @pytest.mark.live_phase("LocationOperations", "reorder")
    def test_swap_two_temp_locations(self, writable_project):
        """Create two locations, swap via MoveTo, restore."""
        name_a = "TEST_loc_phase_c_swap_a"
        name_b = "TEST_loc_phase_c_swap_b"

        _delete_if_present(writable_project, name_a)
        _delete_if_present(writable_project, name_b)

        loc_a = writable_project.Location.Create(name_a)
        loc_b = writable_project.Location.Create(name_b)
        try:
            possibilities = writable_project.lp.LocationsOA.PossibilitiesOS

            idx_a_initial = possibilities.IndexOf(loc_a)
            idx_b_initial = possibilities.IndexOf(loc_b)
            assert idx_a_initial >= 0
            assert idx_b_initial >= 0
            assert idx_a_initial != idx_b_initial
            assert idx_a_initial < idx_b_initial  # Create() appends

            # Reorder: move loc_a to a position past loc_b. MoveTo's
            # destIndex semantics are "insert before this index"; when
            # moving forward in the same sequence, add 1.
            possibilities.MoveTo(
                idx_a_initial, idx_a_initial, possibilities, idx_b_initial + 1
            )
            assert possibilities.IndexOf(loc_a) > possibilities.IndexOf(loc_b)

            # Restore: move loc_a back to its original index. Moving
            # backward, destIndex is used directly.
            current_idx = possibilities.IndexOf(loc_a)
            possibilities.MoveTo(
                current_idx, current_idx, possibilities, idx_a_initial
            )
            assert possibilities.IndexOf(loc_a) == idx_a_initial
            assert possibilities.IndexOf(loc_b) == idx_b_initial
        finally:
            for loc in (loc_a, loc_b):
                try:
                    writable_project.Location.Delete(loc)
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# Phase D: modify + restore (capture-restore name change)
# ---------------------------------------------------------------------------


class TestLocationsPhaseDModify:
    """
    Phase D: capture name, set new value, assert change, restore
    original. Note: DateModified is auto-bumped by LCM on any write, so
    the location is XML-dirty even though the user-visible name returned
    to the captured value. Accepted (see CLAUDE.md Phase D note);
    scripts/restore_sena3.py wipes the churn between sessions.
    """

    @pytest.mark.live_phase("LocationOperations", "modify")
    def test_name_capture_modify_restore(self, writable_project):
        """SetName(new) then SetName(captured) round-trips the value."""
        name = "TEST_loc_phase_d_modify"
        new_name = "TEST_loc_phase_d_modified"

        _delete_if_present(writable_project, name)
        _delete_if_present(writable_project, new_name)

        location = writable_project.Location.Create(name)
        try:
            captured = writable_project.Location.GetName(location)
            assert captured == name

            writable_project.Location.SetName(location, new_name)
            assert writable_project.Location.GetName(location) == new_name

            writable_project.Location.SetName(location, captured)
            assert writable_project.Location.GetName(location) == name
        finally:
            try:
                writable_project.Location.Delete(location)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Phase E: delete pre-existing (N/A for LocationOperations on Sena 3)
# ---------------------------------------------------------------------------


class TestLocationsPhaseEDelete:
    """
    Phase E exists for testing destructive delete against pre-existing
    project data -- the case where create-then-delete (Phase B) is not
    sufficient because the deletion target wasn't created by the test.

    Sena 3 ships with zero existing locations, so for LocationOperations
    this phase has no meaningful target. The Phase B test already covers
    Delete's behaviour on TEST_ objects we created ourselves. A
    sandbox-only test that creates and deletes inside the sandbox would
    duplicate Phase B with no extra signal.

    When this template is replicated to a class that DOES have
    pre-existing items in Sena 3 (PersonOperations has 6, PhonemeOperations
    has 44, etc.), Phase E should: (a) snapshot one pre-existing item's
    properties, (b) delete it in the sena3_sandbox fixture, (c) confirm
    Find returns None, (d) reopen and confirm persistence. The sandbox
    keeps the user's real project untouched.
    """

    @pytest.mark.live_phase("LocationOperations", "delete")
    @pytest.mark.skip(
        reason=(
            "N/A: Sena 3 has zero pre-existing locations. Phase B already "
            "covers Delete on test-created objects; sandbox-only delete "
            "of a self-created object would duplicate Phase B."
        )
    )
    def test_delete_preexisting_in_sandbox(self, sena3_sandbox):
        """Placeholder: see class docstring for the replication pattern."""
        ...
