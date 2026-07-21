#
#   test_msa_remove_orphaned.py
#
#   Class: TestRemoveOrphaned
#          Mock-based unit tests for MSAOperations.RemoveOrphaned
#          (issue #206: project-wide WfiMorphBundle-aware MSA orphan
#          cleanup).
#
#   Uses list-backed fake LCM objects (no live FieldWorks project
#   required for these); one dedicated test exercises the real
#   ILexEntry cast failure path and therefore needs SIL.LCModel to be
#   importable (provided by the session fixture in tests/conftest.py).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import contextlib
import os
import sys
from unittest.mock import Mock, patch

import pytest

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from flexicon.code.Lexicon.MSAOperations import MSAOperations
from flexicon.code.FLExProject import FP_ReadOnlyError, FP_ParameterError
from SIL.LCModel import ILexEntryRepository, IWfiMorphBundleRepository


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakeMSA:
    """Minimal stand-in for an IMoXxxMsa: Hvo/ClassName/IsValidObject only."""

    def __init__(self, hvo, class_name="MoStemMsa", valid=True):
        self.Hvo = hvo
        self.ClassName = class_name
        self.IsValidObject = valid


class FakeMSAOwningCollection(list):
    """list-backed stand-in for ILexEntry.MorphoSyntaxAnalysesOC."""

    def Remove(self, item):
        self.remove(item)


class FakeSense:
    def __init__(self, msa=None):
        self.MorphoSyntaxAnalysisRA = msa


class FakeEntry:
    def __init__(self, hvo, senses=None, msas=None):
        self.Hvo = hvo
        self.SensesOS = senses or []
        self.MorphoSyntaxAnalysesOC = FakeMSAOwningCollection(msas or [])


class FakeBundle:
    def __init__(self, msa=None):
        self.MsaRA = msa


def _make_project(entries, bundles, write_enabled=True):
    """Build a minimal mock FLExProject sufficient to drive RemoveOrphaned()."""
    project = Mock()
    project.writeEnabled = write_enabled

    def _objects_in(repo):
        if repo is ILexEntryRepository:
            return iter(entries)
        if repo is IWfiMorphBundleRepository:
            return iter(bundles)
        return iter([])

    project.ObjectsIn = Mock(side_effect=_objects_in)
    return project


def _make_ops(entries, bundles, write_enabled=True):
    project = _make_project(entries, bundles, write_enabled=write_enabled)
    ops = MSAOperations(project)
    # Bypass the real transaction machinery -- not under test here.
    ops._TransactionCM = Mock(return_value=contextlib.nullcontext())
    return ops, project


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRemoveOrphanedProjectWide:
    """entry=None -> sweep over every entry returned by ObjectsIn()."""

    def test_orphan_removed(self):
        """An MSA referenced by neither a sense nor a bundle is removed."""
        orphan = FakeMSA(101, "MoStemMsa")
        entry = FakeEntry(1, senses=[], msas=[orphan])
        ops, project = _make_ops([entry], bundles=[])

        result = ops.RemoveOrphaned()

        assert result.removed_count == 1
        assert result.kept_count == 0
        assert len(result.removed) == 1
        assert result.removed[0].entry_hvo == 1
        assert result.removed[0].msa_hvo == 101
        assert result.removed[0].class_name == "MoStemMsa"
        assert orphan not in entry.MorphoSyntaxAnalysesOC

    def test_sense_referenced_kept(self):
        """An MSA referenced by an entry-local sense is kept."""
        msa = FakeMSA(102, "MoDerivAffMsa")
        sense = FakeSense(msa=msa)
        entry = FakeEntry(2, senses=[sense], msas=[msa])
        ops, project = _make_ops([entry], bundles=[])

        result = ops.RemoveOrphaned()

        assert result.removed_count == 0
        assert result.kept_count == 1
        assert result.removed == []
        assert msa in entry.MorphoSyntaxAnalysesOC

    def test_bundle_referenced_kept(self):
        """An MSA referenced only by a project-wide morph bundle is kept."""
        msa = FakeMSA(103, "MoInflAffMsa")
        entry = FakeEntry(3, senses=[], msas=[msa])
        bundle = FakeBundle(msa=msa)
        ops, project = _make_ops([entry], bundles=[bundle])

        result = ops.RemoveOrphaned()

        assert result.removed_count == 0
        assert result.kept_count == 1
        assert msa in entry.MorphoSyntaxAnalysesOC

    def test_mixed_orphan_sense_and_bundle_referenced(self):
        """One orphan, one sense-kept, one bundle-kept, in the same entry."""
        orphan = FakeMSA(201, "MoStemMsa")
        sense_kept = FakeMSA(202, "MoDerivAffMsa")
        bundle_kept = FakeMSA(203, "MoUnclassifiedAffixMsa")
        sense = FakeSense(msa=sense_kept)
        entry = FakeEntry(20, senses=[sense], msas=[orphan, sense_kept, bundle_kept])
        bundle = FakeBundle(msa=bundle_kept)
        ops, project = _make_ops([entry], bundles=[bundle])

        result = ops.RemoveOrphaned()

        assert result.removed_count == 1
        assert result.kept_count == 2
        assert [r.msa_hvo for r in result.removed] == [201]
        remaining = {m.Hvo for m in entry.MorphoSyntaxAnalysesOC}
        assert remaining == {202, 203}

    def test_by_entry_breakdown(self):
        """by_entry has one row per entry that owned >=1 MSA."""
        orphan = FakeMSA(301)
        kept = FakeMSA(302)
        sense = FakeSense(msa=kept)
        entry_with_msas = FakeEntry(30, senses=[sense], msas=[orphan, kept])
        entry_without_msas = FakeEntry(31, senses=[], msas=[])
        ops, project = _make_ops([entry_with_msas, entry_without_msas], bundles=[])

        result = ops.RemoveOrphaned()

        assert len(result.by_entry) == 1
        row = result.by_entry[0]
        assert row.entry_hvo == 30
        assert row.removed_count == 1
        assert row.kept_count == 1

    def test_already_invalid_msa_is_skipped_not_removed_or_kept(self):
        """
        An orphan candidate whose IsValidObject is already False (e.g.
        cascade-deleted by LCM) is neither counted as removed nor kept,
        and .Remove() is never called on it.
        """
        stale = FakeMSA(401, valid=False)
        entry = FakeEntry(40, senses=[], msas=[stale])
        ops, project = _make_ops([entry], bundles=[])

        result = ops.RemoveOrphaned()

        assert result.removed_count == 0
        assert result.kept_count == 0
        assert result.removed == []
        # Untouched -- Remove() was never called for the stale MSA.
        assert stale in entry.MorphoSyntaxAnalysesOC

    def test_performance_single_pass_over_bundles(self):
        """
        Bundles are enumerated exactly once (project.ObjectsIn is called
        once for IWfiMorphBundleRepository), regardless of the number of
        entries/MSAs scanned -- guards against an O(MSAs x bundles) scan.
        """
        entries = [
            FakeEntry(i, senses=[], msas=[FakeMSA(1000 + i)]) for i in range(5)
        ]
        ops, project = _make_ops(entries, bundles=[])

        ops.RemoveOrphaned()

        bundle_calls = [
            c for c in project.ObjectsIn.call_args_list
            if c.args and c.args[0] is IWfiMorphBundleRepository
        ]
        assert len(bundle_calls) == 1


class TestRemoveOrphanedEntryScoped:
    """entry=<ILexEntry-or-hvo> -> only that entry's MSAs are candidates,
    but the bundle cross-check remains project-wide."""

    def test_entry_scoped_removes_only_from_scanned_entry(self):
        orphan_in_scope = FakeMSA(501)
        orphan_out_of_scope = FakeMSA(502)
        scoped_entry = FakeEntry(50, senses=[], msas=[orphan_in_scope])
        other_entry = FakeEntry(51, senses=[], msas=[orphan_out_of_scope])
        ops, project = _make_ops([scoped_entry, other_entry], bundles=[])

        with patch(
            "flexicon.code.Lexicon.MSAOperations.ILexEntry",
            side_effect=lambda x: x,
        ):
            result = ops.RemoveOrphaned(entry=scoped_entry)

        assert result.removed_count == 1
        assert result.removed[0].entry_hvo == 50
        # Out-of-scope entry's MSA must be untouched.
        assert orphan_out_of_scope in other_entry.MorphoSyntaxAnalysesOC

    def test_entry_scoped_still_checks_bundles_project_wide(self):
        """
        Safety-first (issue #206): even when scoped to a single entry, an
        MSA that entry owns but is referenced only by a morph bundle
        elsewhere in the project must be kept, not removed.
        """
        msa = FakeMSA(601)
        scoped_entry = FakeEntry(60, senses=[], msas=[msa])
        bundle = FakeBundle(msa=msa)
        ops, project = _make_ops([scoped_entry], bundles=[bundle])

        with patch(
            "flexicon.code.Lexicon.MSAOperations.ILexEntry",
            side_effect=lambda x: x,
        ):
            result = ops.RemoveOrphaned(entry=scoped_entry)

        assert result.removed_count == 0
        assert result.kept_count == 1
        assert msa in scoped_entry.MorphoSyntaxAnalysesOC

    def test_invalid_entry_raises_parameter_error(self):
        """
        A genuinely un-castable `entry` argument surfaces as
        FP_ParameterError, not a raw pythonnet TypeError. Uses the real
        (unpatched) ILexEntry cast.
        """
        ops, project = _make_ops([], bundles=[])

        with pytest.raises(FP_ParameterError):
            ops.RemoveOrphaned(entry=object())


class TestRemoveOrphanedGuardsAndProgress:
    def test_readonly_guard(self):
        """RemoveOrphaned refuses to run against a read-only project."""
        ops, project = _make_ops([], bundles=[], write_enabled=False)

        with pytest.raises(FP_ReadOnlyError):
            ops.RemoveOrphaned()

    def test_progress_callback_invoked_per_entry(self):
        entries = [FakeEntry(i, senses=[], msas=[]) for i in range(3)]
        ops, project = _make_ops(entries, bundles=[])
        progress = Mock()

        ops.RemoveOrphaned(progress=progress)

        assert progress.call_count == 3
        assert progress.call_args_list == [
            ((1, 3),), ((2, 3),), ((3, 3),)
        ]

    def test_progress_callback_exception_is_swallowed(self):
        """A broken progress callback must not abort the sweep."""
        orphan = FakeMSA(701)
        entry = FakeEntry(70, senses=[], msas=[orphan])
        ops, project = _make_ops([entry], bundles=[])
        progress = Mock(side_effect=RuntimeError("boom"))

        result = ops.RemoveOrphaned(progress=progress)

        assert result.removed_count == 1
        progress.assert_called_once_with(1, 1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
