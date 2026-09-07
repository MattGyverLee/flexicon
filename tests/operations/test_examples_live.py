#
#   test_examples_live.py
#
#   Class: ExampleOperations
#          Live-DB tests against Sena 3 covering all five phases of the
#          stabilization model:
#              A. read-only
#              B. create + delete in-place (TEST_ prefix, finally cleanup)
#              C. reorder (BaseOperations.MoveUp/MoveDown helpers)
#              D. modify (capture-restore)
#              E. delete pre-existing (sandbox copy)
#
#          Examples are owned by ILexSense via sense.ExamplesOS (ordered
#          sequence). ExampleOperations overrides _GetSequence(parent),
#          so BaseOperations.MoveUp/MoveDown helpers work directly --
#          Phase C uses those helpers rather than raw MoveTo calls.
#
#          Sena 3 has 1725 senses; most contain examples, making Phase
#          E genuinely destructive against pre-existing project data.
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


def _first_sense(project):
    """Return the first ILexSense in the project, or None if empty."""
    for entry in project.lexDB.Entries:
        for sense in entry.AllSenses:
            return sense
    return None


def _find_sense_with_existing_examples(project):
    """Return the first ILexSense whose ExamplesOS has at least one entry."""
    for entry in project.lexDB.Entries:
        for sense in entry.AllSenses:
            if sense.ExamplesOS.Count > 0:
                return sense
    return None


def _delete_test_examples(project, sense):
    """Pre-clean: remove any TEST_-prefixed examples owned by sense.

    Note: ExampleOperations.GetExample can return None (its
    _NormalizeMultiString lets None pass through despite the docstring
    promising "" on unset). Guard accordingly.
    """
    # Iterate a snapshot since we're mutating the collection.
    for example in list(sense.ExamplesOS):
        try:
            text = project.Examples.GetExample(example)
        except Exception:
            continue
        if text and text.startswith("TEST_"):
            try:
                project.Examples.Delete(example)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Phase A: read-only
# ---------------------------------------------------------------------------


class TestExamplesPhaseARead:
    """Phase A: getters return without raising."""

    @pytest.mark.live_phase("ExampleOperations", "read")
    def test_get_all_project_wide(self, writable_project):
        """GetAll() with no argument iterates the whole project."""
        # We don't materialize the full list (could be slow on large
        # projects); just confirm the iterator yields at least one or
        # is empty without raising.
        gen = writable_project.Examples.GetAll()
        # Take the first item if any; the iterator should not raise.
        try:
            first = next(iter(gen))
            assert first is not None
        except StopIteration:
            pass  # Empty project: still a valid outcome

    @pytest.mark.live_phase("ExampleOperations", "read")
    def test_get_all_for_specific_sense(self, writable_project):
        """GetAll(sense) returns a list of examples for that sense."""
        sense = _first_sense(writable_project)
        if sense is None:
            pytest.skip("Sandbox project has no senses")
        examples = list(writable_project.Examples.GetAll(sense))
        assert isinstance(examples, list)


# ---------------------------------------------------------------------------
# Phase B: create + delete in-place (TEST_ prefix)
# ---------------------------------------------------------------------------


class TestExamplesPhaseBAdd:
    """Phase B: Create + Delete with try/finally on an arbitrary sense."""

    @pytest.mark.live_phase("ExampleOperations", "add")
    def test_create_and_delete_roundtrip(self, writable_project):
        """Create an example on the first sense, verify, delete."""
        sense = _first_sense(writable_project)
        if sense is None:
            pytest.skip("Sandbox project has no senses")

        _delete_test_examples(writable_project, sense)

        text = "TEST_example_phase_b_roundtrip"
        count_before = sense.ExamplesOS.Count
        example = writable_project.Examples.Create(sense, text)
        try:
            assert example is not None
            assert writable_project.Examples.GetExample(example) == text
            assert sense.ExamplesOS.Count == count_before + 1
        finally:
            # Surface a Delete failure rather than swallowing it; the
            # whole point of the test is to verify the round-trip works.
            writable_project.Examples.Delete(example)

        # Count should be back to original; the specific example gone.
        assert sense.ExamplesOS.Count == count_before


# ---------------------------------------------------------------------------
# Phase C: reorder via BaseOperations.MoveUp / MoveDown helpers
# ---------------------------------------------------------------------------


class TestExamplesPhaseCReorder:
    """
    Phase C: use the BaseOperations.MoveUp / MoveDown helpers, which
    work for ExampleOperations because the class overrides
    _GetSequence(parent) to return parent.ExamplesOS. Internally the
    helpers call LcmOwningSequence.MoveTo (see test_locations_live.py
    for the gotcha when a class does NOT override _GetSequence).
    """

    @pytest.mark.live_phase("ExampleOperations", "reorder")
    def test_movedown_then_moveup_restores_order(self, writable_project):
        """Create two examples, MoveDown the first, MoveUp to restore."""
        sense = _first_sense(writable_project)
        if sense is None:
            pytest.skip("Sandbox project has no senses")

        _delete_test_examples(writable_project, sense)

        text_a = "TEST_example_phase_c_a"
        text_b = "TEST_example_phase_c_b"

        ex_a = writable_project.Examples.Create(sense, text_a)
        ex_b = writable_project.Examples.Create(sense, text_b)
        try:
            seq = sense.ExamplesOS
            idx_a_initial = seq.IndexOf(ex_a)
            idx_b_initial = seq.IndexOf(ex_b)
            assert idx_a_initial >= 0
            assert idx_b_initial >= 0
            assert idx_a_initial < idx_b_initial  # Create appends

            # MoveDown ex_a past ex_b
            moved = writable_project.Examples.MoveDown(sense, ex_a, positions=1)
            assert moved == 1
            assert seq.IndexOf(ex_a) > seq.IndexOf(ex_b)

            # MoveUp ex_a back to original position
            moved_back = writable_project.Examples.MoveUp(sense, ex_a, positions=1)
            assert moved_back == 1
            assert seq.IndexOf(ex_a) == idx_a_initial
            assert seq.IndexOf(ex_b) == idx_b_initial
        finally:
            for ex in (ex_a, ex_b):
                try:
                    writable_project.Examples.Delete(ex)
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# Phase D: modify + restore (Example text via SetExample)
# ---------------------------------------------------------------------------


class TestExamplesPhaseDModify:
    """
    Phase D: create a temp example, capture text, modify, restore.
    Operates on a freshly-created TEST_ example rather than a
    pre-existing Sena 3 example so a mid-test crash leaves no
    visible residue. LCM's DateModified churn is accepted.
    """

    @pytest.mark.live_phase("ExampleOperations", "modify")
    def test_text_capture_modify_restore(self, writable_project):
        """SetExample(new) then SetExample(captured) round-trips."""
        sense = _first_sense(writable_project)
        if sense is None:
            pytest.skip("Sandbox project has no senses")

        _delete_test_examples(writable_project, sense)

        initial = "TEST_example_phase_d_initial"
        modified = "TEST_example_phase_d_modified"

        example = writable_project.Examples.Create(sense, initial)
        try:
            captured = writable_project.Examples.GetExample(example)
            assert captured == initial

            writable_project.Examples.SetExample(example, modified)
            assert writable_project.Examples.GetExample(example) == modified

            writable_project.Examples.SetExample(example, captured)
            assert writable_project.Examples.GetExample(example) == initial
        finally:
            try:
                writable_project.Examples.Delete(example)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Phase E: delete pre-existing example in sandbox
# ---------------------------------------------------------------------------


class TestExamplesPhaseEDelete:
    """
    Phase E: delete a pre-existing ILexExampleSentence inside an
    isolated copy of Sena 3. Sena 3 contains real example data
    across its 1725 senses, so this exercises the destructive
    cascade-removal path against real project content -- without
    touching the user's real Sena 3.
    """

    @pytest.mark.live_phase("ExampleOperations", "delete")
    def test_delete_preexisting_example_in_sandbox(self, sena3_sandbox):
        """Find a pre-existing example, delete it, confirm gone."""
        sense = _find_sense_with_existing_examples(sena3_sandbox)
        if sense is None:
            pytest.skip(
                "Sandbox project has no senses with pre-existing examples"
            )

        examples_before = list(sense.ExamplesOS)
        count_before = len(examples_before)
        assert count_before >= 1

        victim = examples_before[0]
        victim_text = sena3_sandbox.Examples.GetExample(victim)
        victim_guid = sena3_sandbox.Examples.GetGuid(victim)

        sena3_sandbox.Examples.Delete(victim)

        # Confirm: count dropped by one, victim no longer in sequence.
        count_after = sense.ExamplesOS.Count
        assert count_after == count_before - 1, (
            f"Expected {count_before - 1} examples after delete, "
            f"got {count_after}"
        )
        # Victim should not be in the remaining list (LCM doesn't always
        # raise on IndexOf for deleted objects, so check by identity).
        remaining_ids = {id(ex) for ex in sense.ExamplesOS}
        assert id(victim) not in remaining_ids

        # GUID was captured before delete -- this assertion exists to
        # document what we snapshotted, not to test post-delete state.
        assert victim_guid is not None
        assert victim_text is not None
