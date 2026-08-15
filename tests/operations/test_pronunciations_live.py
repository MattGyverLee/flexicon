#
#   test_pronunciations_live.py
#
#   Class: PronunciationOperations
#          Live-DB tests against Sena 3 covering all five phases of the
#          stabilization model:
#              A. read-only
#              B. create + delete in-place (TEST_ prefix, finally cleanup)
#              C. reorder via BaseOperations.MoveUp/MoveDown
#              D. modify (capture-restore)
#              E. delete pre-existing (sandbox copy)
#
#          Pronunciations are owned by ILexEntry via entry.PronunciationsOS
#          (LcmOwningSequence<ILexPronunciation>). PronunciationOperations
#          overrides _GetSequence to return parent.PronunciationsOS, so
#          BaseOperations.MoveUp / MoveDown work directly (Phase C).
#
#          Create() follows the SAFE ordering: factory.Create() ->
#          PronunciationsOS.Add(...) -> set Form via TsStringUtils. This is
#          the opposite of the broken ordering seen in VariantOperations
#          (issue #151 / Phase B regression note in test_variants_live.py),
#          so Phase B is expected to construct the test pronunciation
#          successfully.
#
#          However, per issue #151 PronunciationOperations.Delete (L248-250),
#          Duplicate (L308 + 315/321), and GetOwningEntry (L958) still ship
#          the unfixed `.Owner-without-cast + hasattr-guarded
#          PronunciationsOS` pattern:
#
#              entry = pronunciation.Owner               # ICmObject base
#              if hasattr(entry, "PronunciationsOS"):    # False on ICmObject
#                  entry.PronunciationsOS.Remove(...)    # never executes
#
#          Phase B's `finally Delete` is therefore expected to silently
#          no-op -- the pronunciation leaks and the post-finally
#          `Count == count_before` assertion will FAIL, surfacing the
#          P1 bug as documented. Phase C cleanup, Phase D cleanup, and
#          Phase E (delete a pre-existing pronunciation) hit the same
#          shape.
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _first_entry_with_lexeme_form(project):
    """
    Return the first ILexEntry that has a LexemeFormOA.

    Pronunciation.Create() doesn't require a particular morph type, but
    grounding test data on an entry with a populated lexeme form keeps
    the live project semantically valid.
    """
    for entry in project.lexDB.Entries:
        if entry.LexemeFormOA:
            return entry
    return None


def _first_entry_with_pronunciations(project):
    """
    Return the first ILexEntry whose PronunciationsOS has at least one
    item. Used by Phase E to find a pre-existing delete target.
    """
    for entry in project.lexDB.Entries:
        if (
            hasattr(entry, "PronunciationsOS")
            and entry.PronunciationsOS.Count > 0
        ):
            return entry
    return None


def _delete_test_pronunciations(project, entry):
    """
    Pre-clean: remove TEST_-prefixed pronunciations from
    entry.PronunciationsOS that may have leaked from a crashed prior
    run. Calls Delete via the Operations API so the cleanup itself
    exercises the same pathway as production.

    Note: if PronunciationOperations.Delete still has the
    `.Owner-without-cast + hasattr-guarded PronunciationsOS` bug from
    issue #151, this pre-clean will silently no-op. The TEST_ forms
    accumulate across runs; the Sena 3 restore script wipes them
    between sessions. We fall back to a direct OS-list Remove() so
    a stale TEST_ pronunciation can't poison subsequent test runs.
    """
    for pron in list(entry.PronunciationsOS):
        try:
            form = project.Pronunciations.GetForm(pron)
        except Exception:
            continue
        if form and form.startswith("TEST_"):
            try:
                project.Pronunciations.Delete(pron)
            except Exception:
                pass
            # Direct fallback so stale data can't poison the next run.
            try:
                if pron in entry.PronunciationsOS:
                    entry.PronunciationsOS.Remove(pron)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Phase A: read-only
# ---------------------------------------------------------------------------


class TestPronunciationsPhaseARead:
    """Phase A: getters return without raising, regardless of count."""

    @pytest.mark.live_phase("PronunciationOperations", "read")
    def test_get_all_project_wide(self, writable_project):
        """GetAll() with no argument iterates the whole project."""
        gen = writable_project.Pronunciations.GetAll()
        try:
            first = next(iter(gen))
            assert first is not None
        except StopIteration:
            # Project might have zero pronunciations; that's still a pass.
            pass

    @pytest.mark.live_phase("PronunciationOperations", "read")
    def test_get_all_for_specific_entry(self, writable_project):
        """GetAll(entry) returns an iterable for one entry without raising."""
        entry = _first_entry_with_lexeme_form(writable_project)
        if entry is None:
            pytest.skip("Project has no entries with LexemeFormOA")
        collection = writable_project.Pronunciations.GetAll(entry)
        # May be empty if entry has no pronunciations; just confirm iterable.
        items = list(collection)
        assert isinstance(items, list)


# ---------------------------------------------------------------------------
# Phase B: create + delete in-place (operates on PronunciationsOS)
# ---------------------------------------------------------------------------


class TestPronunciationsPhaseBAdd:
    """
    Phase B: Create + Delete a TEST_ pronunciation on an arbitrary entry.

    Create() in PronunciationOperations follows the SAFE ordering --
    factory.Create() -> PronunciationsOS.Add(pron) -> set Form via
    TsStringUtils -- so creation should succeed cleanly. The expected
    failure is in the finally `Delete`: per issue #151 L248-250, Delete
    reads `pronunciation.Owner` without casting to ILexEntry, then
    `hasattr(entry, "PronunciationsOS")` returns False on ICmObject and
    the Remove() call never executes. The post-finally count assertion
    therefore surfaces a silent no-op.
    """

    @pytest.mark.live_phase("PronunciationOperations", "add")
    def test_create_and_delete_roundtrip(self, writable_project):
        """Create on entry -> verify form -> delete -> verify count restored."""
        entry = _first_entry_with_lexeme_form(writable_project)
        if entry is None:
            pytest.skip("Project has no entries with LexemeFormOA")

        _delete_test_pronunciations(writable_project, entry)

        form = "TEST_pron_phase_b_roundtrip"
        count_before = entry.PronunciationsOS.Count
        pronunciation = writable_project.Pronunciations.Create(entry, form)
        try:
            assert pronunciation is not None
            assert writable_project.Pronunciations.GetForm(pronunciation) == form
            assert entry.PronunciationsOS.Count == count_before + 1
        finally:
            # Surface a Delete failure rather than swallow it (per template).
            writable_project.Pronunciations.Delete(pronunciation)

        assert entry.PronunciationsOS.Count == count_before


# ---------------------------------------------------------------------------
# Phase C: reorder via BaseOperations.MoveUp / MoveDown
# ---------------------------------------------------------------------------


class TestPronunciationsPhaseCReorder:
    """
    Phase C: PronunciationOperations overrides _GetSequence to return
    parent.PronunciationsOS, so MoveUp / MoveDown work directly through
    the standard BaseOperations helpers (identical shape to
    AllomorphOperations Phase C).

    The test creates two TEST_ pronunciations, swaps their order via
    MoveDown then restores via MoveUp, and cleans up in `finally`. The
    cleanup `Delete` calls hit the same #151 bug as Phase B; the cleanup
    block swallows the resulting no-op so failures here are attributable
    to the reorder itself, not to teardown.
    """

    @pytest.mark.live_phase("PronunciationOperations", "reorder")
    def test_movedown_then_moveup_restores_order(self, writable_project):
        """Create two pronunciations, swap them, restore."""
        entry = _first_entry_with_lexeme_form(writable_project)
        if entry is None:
            pytest.skip("Project has no entries with LexemeFormOA")

        _delete_test_pronunciations(writable_project, entry)

        form_a = "TEST_pron_phase_c_a"
        form_b = "TEST_pron_phase_c_b"

        pron_a = writable_project.Pronunciations.Create(entry, form_a)
        pron_b = writable_project.Pronunciations.Create(entry, form_b)
        try:
            seq = entry.PronunciationsOS
            idx_a_initial = seq.IndexOf(pron_a)
            idx_b_initial = seq.IndexOf(pron_b)
            assert idx_a_initial >= 0
            assert idx_b_initial >= 0
            assert idx_a_initial < idx_b_initial  # Create appends

            writable_project.Pronunciations.MoveDown(
                entry, pron_a, positions=1
            )
            assert seq.IndexOf(pron_a) > seq.IndexOf(pron_b)

            writable_project.Pronunciations.MoveUp(
                entry, pron_a, positions=1
            )
            assert seq.IndexOf(pron_a) == idx_a_initial
            assert seq.IndexOf(pron_b) == idx_b_initial
        finally:
            for pron in (pron_a, pron_b):
                try:
                    writable_project.Pronunciations.Delete(pron)
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# Phase D: modify + restore (form text via SetForm)
# ---------------------------------------------------------------------------


class TestPronunciationsPhaseDModify:
    """
    Phase D: SetForm(new) then SetForm(captured) round-trips the form
    text on the default vernacular writing system. Unlike VariantOperations,
    PronunciationOperations.GetForm / SetForm read and write the
    pronunciation object's own MultiString.Form directly -- there's no
    .Owner indirection -- so this phase should round-trip cleanly.

    DateModified will still be bumped by LCM on each write, so the
    pronunciation is XML-dirty after this test even though the user-
    visible form text is restored. That's accepted per the
    test_locations_live.py Phase D note; scripts/restore_sena3.py
    wipes the churn between sessions.
    """

    @pytest.mark.live_phase("PronunciationOperations", "modify")
    def test_form_capture_modify_restore(self, writable_project):
        """Capture form via GetForm, SetForm(new), SetForm(captured)."""
        entry = _first_entry_with_lexeme_form(writable_project)
        if entry is None:
            pytest.skip("Project has no entries with LexemeFormOA")

        _delete_test_pronunciations(writable_project, entry)

        initial = "TEST_pron_phase_d_initial"
        modified = "TEST_pron_phase_d_modified"

        pronunciation = writable_project.Pronunciations.Create(entry, initial)
        try:
            captured = writable_project.Pronunciations.GetForm(pronunciation)
            assert captured == initial

            writable_project.Pronunciations.SetForm(pronunciation, modified)
            assert (
                writable_project.Pronunciations.GetForm(pronunciation)
                == modified
            )

            writable_project.Pronunciations.SetForm(pronunciation, captured)
            assert (
                writable_project.Pronunciations.GetForm(pronunciation)
                == initial
            )
        finally:
            try:
                writable_project.Pronunciations.Delete(pronunciation)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Phase E: delete pre-existing pronunciation in sandbox
# ---------------------------------------------------------------------------


class TestPronunciationsPhaseEDelete:
    """
    Phase E: delete a pre-existing ILexPronunciation inside an isolated
    copy of Sena 3. Skips if no entry has pronunciations.

    EXPECTED FAILURE per issue #151: Delete at L248-250 reads
    `pronunciation.Owner` (ICmObject) without casting, then
    `hasattr(entry, "PronunciationsOS")` returns False on the base
    ICmObject interface and the Remove call never executes. The
    post-delete count assertion will catch this as a silent no-op.
    """

    @pytest.mark.live_phase("PronunciationOperations", "delete")
    def test_delete_preexisting_pronunciation_in_sandbox(self, sena3_sandbox):
        """Find a pre-existing pronunciation, delete it, confirm count drops."""
        entry = _first_entry_with_pronunciations(sena3_sandbox)
        if entry is None:
            pytest.skip(
                "Sandbox project has no entries with PronunciationsOS items; "
                "cannot exercise Phase E"
            )

        count_before = entry.PronunciationsOS.Count
        assert count_before >= 1

        victim = entry.PronunciationsOS[0]

        sena3_sandbox.Pronunciations.Delete(victim)

        count_after = entry.PronunciationsOS.Count
        assert count_after == count_before - 1, (
            f"Expected {count_before - 1} pronunciations after delete, "
            f"got {count_after}"
        )
