#
#   test_etymologies_live.py
#
#   Class: EtymologyOperations
#          Live-DB tests against Sena 3 covering all five phases of the
#          stabilization model:
#              A. read-only
#              B. create + delete in-place (TEST_ prefix, finally cleanup)
#              C. reorder via BaseOperations.MoveUp/MoveDown
#              D. modify (capture-restore form)
#              E. delete pre-existing (sandbox copy)
#
#          Etymologies are owned by ILexEntry via entry.EtymologyOS
#          (LcmOwningSequence<ILexEtymology>). EtymologyOperations
#          overrides _GetSequence to return parent.EtymologyOS, so
#          BaseOperations.MoveUp / MoveDown work directly (Phase C).
#
#          EtymologyOperations is CLEAN per issue #151: both Delete
#          (L277) and Duplicate (L337) use _GetTypedOwner so the
#          casting fix from #98 is already applied. Comments at
#          L272-276 and L333-335 document the post-#98 shape
#          explicitly. Phase B teardown and Phase E delete are
#          therefore expected to PASS rather than silently no-op
#          like PronunciationOperations.
#
#          CORRECTED 2026-08-18 (live-reflection): ILexEtymology has NO
#          "Source" field at all -- the claim below and in the old
#          CLAUDE.md Category 8 table that it was an IMultiString was
#          wrong. GetSource/SetSource/Create(source=...) now read/write
#          the real backing field, LanguageNotes (IMultiString), while
#          keeping the same public Get/SetSource surface; see
#          EtymologyOperations.py and docs/API_ISSUES_CATEGORIZED.md
#          Category 8 (corrected) for the detail. Form, Gloss, Comment,
#          and Bibliography on ILexEtymology remain IMultiString as
#          described. Phase D modifies Form via SetForm/GetForm, which
#          uses the standard get_String/set_String pair.
#
#          Create() follows the SAFE ordering: factory.Create() ->
#          EtymologyOS.Add(etym) -> set LanguageNotes/Form/Gloss via
#          TsStringUtils -- the opposite of the broken ordering in
#          VariantOperations, so Phase B construction is expected to
#          succeed cleanly.
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
        from flexlibs2.code.FLExProject import FLExProject
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

    Etymology.Create() does not require a particular morph type, but
    grounding test data on an entry with a populated lexeme form keeps
    the live project semantically valid (an etymology dangling off an
    entry without a headword would be nonsensical to a linguist).
    """
    for entry in project.lexDB.Entries:
        if entry.LexemeFormOA:
            return entry
    return None


def _first_entry_with_etymologies(project):
    """
    Return the first ILexEntry whose EtymologyOS has at least one
    item. Used by Phase E to find a pre-existing delete target.
    """
    for entry in project.lexDB.Entries:
        if (
            hasattr(entry, "EtymologyOS")
            and entry.EtymologyOS.Count > 0
        ):
            return entry
    return None


def _delete_test_etymologies(project, entry):
    """
    Pre-clean: remove TEST_-prefixed etymologies from entry.EtymologyOS
    that may have leaked from a crashed prior run. Uses GetForm to
    identify TEST_ etyms; if a prior run partially constructed an etym
    with no form set, the heuristic misses it -- but Sena 3 is restored
    between sessions via scripts/restore_sena3.py, so that's acceptable.

    EtymologyOperations.Delete is clean per #151 (uses _GetTypedOwner),
    so unlike the PronunciationOperations equivalent this pre-clean
    actually removes the leaked items rather than silently no-opping.
    """
    for etym in list(entry.EtymologyOS):
        try:
            form = project.Etymology.GetForm(etym)
        except Exception:
            continue
        if form and form.startswith("TEST_"):
            try:
                project.Etymology.Delete(etym)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Phase A: read-only
# ---------------------------------------------------------------------------


class TestEtymologiesPhaseARead:
    """Phase A: getters return without raising, regardless of count."""

    @pytest.mark.live_phase("EtymologyOperations", "read")
    def test_get_all_project_wide(self, writable_project):
        """GetAll() with no argument iterates the whole project."""
        gen = writable_project.Etymology.GetAll()
        try:
            first = next(iter(gen))
            assert first is not None
        except StopIteration:
            # Project might have zero etymologies; still a pass.
            pass

    @pytest.mark.live_phase("EtymologyOperations", "read")
    def test_get_all_for_specific_entry(self, writable_project):
        """GetAll(entry) returns an iterable for one entry without raising."""
        entry = _first_entry_with_lexeme_form(writable_project)
        if entry is None:
            pytest.skip("Project has no entries with LexemeFormOA")
        collection = writable_project.Etymology.GetAll(entry)
        # May be empty if entry has no etymologies; just confirm iterable.
        items = list(collection)
        assert isinstance(items, list)


# ---------------------------------------------------------------------------
# Phase B: create + delete in-place (operates on EtymologyOS)
# ---------------------------------------------------------------------------


class TestEtymologiesPhaseBAdd:
    """
    Phase B: Create + Delete a TEST_ etymology on an arbitrary entry.

    EtymologyOperations.Create follows the SAFE ordering --
    factory.Create() -> EtymologyOS.Add(etym) -> set Source/Form/Gloss
    via TsStringUtils -- so creation should succeed cleanly. Delete
    at L277 uses _GetTypedOwner (post-#98 fix) so the finally cleanup
    actually removes the etymology rather than silently no-opping
    like PronunciationOperations does (#151).

    Both the inner count check and the post-finally count assertion
    are expected to PASS.
    """

    @pytest.mark.live_phase("EtymologyOperations", "add")
    def test_create_and_delete_roundtrip(self, writable_project):
        """Create on entry -> verify form -> delete -> verify count restored."""
        entry = _first_entry_with_lexeme_form(writable_project)
        if entry is None:
            pytest.skip("Project has no entries with LexemeFormOA")

        _delete_test_etymologies(writable_project, entry)

        form = "TEST_etym_phase_b_roundtrip"
        count_before = entry.EtymologyOS.Count
        etymology = writable_project.Etymology.Create(entry, form=form)
        try:
            assert etymology is not None
            assert writable_project.Etymology.GetForm(etymology) == form
            assert entry.EtymologyOS.Count == count_before + 1
        finally:
            # Surface a Delete failure rather than swallow it (per template).
            writable_project.Etymology.Delete(etymology)

        assert entry.EtymologyOS.Count == count_before


# ---------------------------------------------------------------------------
# Phase C: reorder via BaseOperations.MoveUp / MoveDown
# ---------------------------------------------------------------------------


class TestEtymologiesPhaseCReorder:
    """
    Phase C: EtymologyOperations overrides _GetSequence to return
    parent.EtymologyOS (L93-98), so MoveUp / MoveDown work directly
    through the standard BaseOperations helpers (identical shape to
    AllomorphOperations and PronunciationOperations Phase C).
    """

    @pytest.mark.live_phase("EtymologyOperations", "reorder")
    def test_movedown_then_moveup_restores_order(self, writable_project):
        """Create two etymologies, swap them, restore."""
        entry = _first_entry_with_lexeme_form(writable_project)
        if entry is None:
            pytest.skip("Project has no entries with LexemeFormOA")

        _delete_test_etymologies(writable_project, entry)

        form_a = "TEST_etym_phase_c_a"
        form_b = "TEST_etym_phase_c_b"

        etym_a = writable_project.Etymology.Create(entry, form=form_a)
        etym_b = writable_project.Etymology.Create(entry, form=form_b)
        try:
            seq = entry.EtymologyOS
            idx_a_initial = seq.IndexOf(etym_a)
            idx_b_initial = seq.IndexOf(etym_b)
            assert idx_a_initial >= 0
            assert idx_b_initial >= 0
            assert idx_a_initial < idx_b_initial  # Create appends

            writable_project.Etymology.MoveDown(entry, etym_a, positions=1)
            assert seq.IndexOf(etym_a) > seq.IndexOf(etym_b)

            writable_project.Etymology.MoveUp(entry, etym_a, positions=1)
            assert seq.IndexOf(etym_a) == idx_a_initial
            assert seq.IndexOf(etym_b) == idx_b_initial
        finally:
            for etym in (etym_a, etym_b):
                try:
                    writable_project.Etymology.Delete(etym)
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# Phase D: modify + restore (form text via SetForm)
# ---------------------------------------------------------------------------


class TestEtymologiesPhaseDModify:
    """
    Phase D: SetForm(new) then SetForm(captured) round-trips the
    etymology's Form on the default analysis writing system.

    EtymologyOperations.GetForm / SetForm read and write
    etymology.Form directly through get_String/set_String on the
    IMultiString accessor -- no .Owner indirection -- so this phase
    should round-trip cleanly.

    Per CLAUDE.md "Category 8: Same-name fields with different LCM
    types": Form on ILexEtymology is an IMultiString (consistent
    with Source, Gloss, Comment, Bibliography on the same type).
    The accessor under test here is therefore the IMultiString shape,
    not the ITsString shape seen on ILexSense.Source.

    DateModified will still be bumped by LCM on each write, so the
    etymology is XML-dirty after this test even though the user-
    visible Form text is restored. Accepted per the test_locations_live
    and test_pronunciations_live Phase D notes; restore_sena3.py wipes
    the churn between sessions.
    """

    @pytest.mark.live_phase("EtymologyOperations", "modify")
    def test_form_capture_modify_restore(self, writable_project):
        """Capture form via GetForm, SetForm(new), SetForm(captured)."""
        entry = _first_entry_with_lexeme_form(writable_project)
        if entry is None:
            pytest.skip("Project has no entries with LexemeFormOA")

        _delete_test_etymologies(writable_project, entry)

        initial = "TEST_etym_phase_d_initial"
        modified = "TEST_etym_phase_d_modified"

        etymology = writable_project.Etymology.Create(entry, form=initial)
        try:
            captured = writable_project.Etymology.GetForm(etymology)
            assert captured == initial

            writable_project.Etymology.SetForm(etymology, modified)
            assert (
                writable_project.Etymology.GetForm(etymology) == modified
            )

            writable_project.Etymology.SetForm(etymology, captured)
            assert (
                writable_project.Etymology.GetForm(etymology) == initial
            )
        finally:
            try:
                writable_project.Etymology.Delete(etymology)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Phase E: delete pre-existing etymology in sandbox
# ---------------------------------------------------------------------------


class TestEtymologiesPhaseEDelete:
    """
    Phase E: delete a pre-existing ILexEtymology inside an isolated
    copy of Sena 3. Skips if no entry has etymologies -- Sena 3 ships
    with relatively few populated etymologies, so the skip path is
    realistic.

    EtymologyOperations.Delete uses _GetTypedOwner (post-#98 fix), so
    this phase is expected to PASS -- in contrast to
    PronunciationOperations Phase E which still silently no-ops.
    """

    @pytest.mark.live_phase("EtymologyOperations", "delete")
    def test_delete_preexisting_etymology_in_sandbox(self, sena3_sandbox):
        """Find a pre-existing etymology, delete it, confirm count drops."""
        entry = _first_entry_with_etymologies(sena3_sandbox)
        if entry is None:
            pytest.skip(
                "Sandbox project has no entries with EtymologyOS items; "
                "cannot exercise Phase E"
            )

        count_before = entry.EtymologyOS.Count
        assert count_before >= 1

        victim = entry.EtymologyOS[0]

        sena3_sandbox.Etymology.Delete(victim)

        count_after = entry.EtymologyOS.Count
        assert count_after == count_before - 1, (
            f"Expected {count_before - 1} etymologies after delete, "
            f"got {count_after}"
        )
