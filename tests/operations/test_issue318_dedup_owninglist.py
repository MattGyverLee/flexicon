#
#   test_issue318_dedup_owninglist.py
#
#   Class: LexEntryOperations / LexSenseOperations
#          Regression coverage for issue #318: MergeObject()'s
#          auto-deduplication of pronunciations, allomorphs, and examples
#          called `dupe.OwningList.Remove(dupe)`. `OwningList` exists only
#          on `ICmPossibility` in LCM 11 -- never on `ILexPronunciation`,
#          `IMoForm`, or `ILexExampleSentence` -- so every removal attempt
#          raised `AttributeError`, which a broad `except Exception:
#          logger.warning(...)` swallowed. Dedup has never functioned;
#          `removed_count` stayed 0 while the merge appeared to succeed.
#
#          Fix: remove via the correct owning sequence
#          (entry.PronunciationsOS / entry.AlternateFormsOS /
#          sense.ExamplesOS). These tests call the real private dedup
#          helpers directly (name-mangled, matching the pattern the
#          production code itself already uses at
#          LexEntryOperations.py:3013,
#          `sense_ops._LexSenseOperations__GetSenseSignature`), against
#          real LexEntryOperations/LexSenseOperations instances with a
#          mocked project -- not a reimplementation of the fix -- so a
#          regression in the actual shipped code fails these tests.
#
#          Every assertion re-reads collection length/membership fresh
#          after the call, rather than trusting "no exception was raised"
#          -- that shallower assertion passes against the pre-fix broken
#          code too (the AttributeError was caught and logged, never
#          surfaced).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import sys
import os
from unittest.mock import Mock

import pytest

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
sys.path.insert(0, _project_root)

from tests.operations import (
    mock_flex_project,
    MockLCMObject,
    MockMultiString,
    MockOwningSequence,
)


# ---------------------------------------------------------------------------
# Shared setup helpers
# ---------------------------------------------------------------------------


def _make_ws(handle):
    """A minimal stand-in for an ILgWritingSystem: only .Handle is read."""
    return Mock(Handle=handle)


def _wire_writing_systems(project, handles):
    """
    Wire self.project.project.ServiceLocator.WritingSystems.AllWritingSystems.

    The real LexEntryOperations/LexSenseOperations dedup helpers iterate
    this to build per-item signatures across every writing system.

    This path matters, and an earlier version of this helper got it wrong.
    It wired `project.project.WritingSystemManager`, which does not exist:
    on a real LcmCache the manager hangs off `ServiceLocator`, and the
    enumeration member is `ServiceLocator.WritingSystems.AllWritingSystems`
    (see WritingSystemOperations.GetAll). Because `project.project` is a
    bare Mock here, the wrong path auto-vivified happily and these tests
    passed green against production code that raised AttributeError on
    every real database -- the signature map stayed empty and dedup found
    nothing, for every caller, forever. Keep this mirroring the real
    member chain exactly; if production changes, change it here too rather
    than letting Mock invent a path that cannot exist.
    """
    project.project = Mock()
    project.project.ServiceLocator = Mock()
    project.project.ServiceLocator.WritingSystems = Mock()
    project.project.ServiceLocator.WritingSystems.AllWritingSystems = [
        _make_ws(h) for h in handles
    ]


class _IdentityITsString:
    """
    Patches ITsString(x) -> x for the duration of a test.

    The real ITsString is a pythonnet interface-cast constructor that
    expects a live COM object; it cannot cast a plain Mock. The
    production code always does `ITsString(thing.get_String(handle)).Text`
    immediately, so an identity passthrough is behaviourally equivalent
    for a mock whose `get_String()` already returns something with a
    `.Text` attribute (see MockMultiString.get_String).
    """

    def __call__(self, x):
        return x


# ===========================================================================
# Issue #318a -- Pronunciation dedup (LexEntryOperations)
# ===========================================================================


class TestDeduplicatePronunciationsInEntry:
    def _make_ops(self, monkeypatch, mock_flex_project):
        from flexicon.code.Lexicon import LexEntryOperations as mod

        monkeypatch.setattr(mod, "ITsString", _IdentityITsString())
        _wire_writing_systems(mock_flex_project, handles=[1])
        return mod.LexEntryOperations(mock_flex_project), mod

    def test_duplicate_pronunciation_is_actually_removed(self, monkeypatch, mock_flex_project):
        """
        Pre-fix: dupe.OwningList.Remove(dupe) raised AttributeError,
        swallowed by the outer catch-all -- PronunciationsOS length never
        changed. Post-fix: the duplicate is actually removed and the
        survivor is the kept master (compared by Hvo), not merely "no
        exception raised".
        """
        ops, _mod = self._make_ops(monkeypatch, mock_flex_project)

        master = MockLCMObject(hvo=100)
        master.Form = MockMultiString({1: "apple"})
        dupe = MockLCMObject(hvo=101)
        dupe.Form = MockMultiString({1: "apple"})

        entry = MockLCMObject(hvo=1000)
        entry.PronunciationsOS = MockOwningSequence([master, dupe])

        before_count = len(list(entry.PronunciationsOS))
        assert before_count == 2

        ops._LexEntryOperations__DeduplicatePronunciationsInEntry(entry)

        after = list(entry.PronunciationsOS)
        assert len(after) == 1, (
            "Duplicate pronunciation was not removed -- PronunciationsOS "
            "length is unchanged, the exact silent-no-op shape of #318."
        )
        assert after[0].Hvo == master.Hvo, "Survivor must be the kept master, not the duplicate."

    def test_no_duplicates_does_not_raise(self, monkeypatch, mock_flex_project):
        """Distinct pronunciations: 0 found, 0 removed -- must not raise."""
        ops, _mod = self._make_ops(monkeypatch, mock_flex_project)

        p1 = MockLCMObject(hvo=100)
        p1.Form = MockMultiString({1: "apple"})
        p2 = MockLCMObject(hvo=101)
        p2.Form = MockMultiString({1: "banana"})

        entry = MockLCMObject(hvo=1000)
        entry.PronunciationsOS = MockOwningSequence([p1, p2])

        ops._LexEntryOperations__DeduplicatePronunciationsInEntry(entry)

        assert len(list(entry.PronunciationsOS)) == 2

    def test_removal_that_silently_fails_raises_fp_deduplication_error(
        self, monkeypatch, mock_flex_project
    ):
        """
        Duplicates WERE detected, but the simulated Remove() call is a
        no-op that neither raises nor actually removes the item (the
        shape of a genuinely benign LCM-side "can't remove yet"
        condition). This must raise FP_DeduplicationError -- "0 removed
        because 0 duplicates existed" and "0 removed because removal
        silently failed" must not collapse into the same silent return
        (the #291 collapse the ticket calls out).
        """
        ops, mod = self._make_ops(monkeypatch, mock_flex_project)

        master = MockLCMObject(hvo=100)
        master.Form = MockMultiString({1: "apple"})
        dupe = MockLCMObject(hvo=101)
        dupe.Form = MockMultiString({1: "apple"})

        entry = MockLCMObject(hvo=1000)
        pron_seq = MockOwningSequence([master, dupe])

        # Simulated benign failure: call succeeds but does not remove.
        pron_seq.Remove = lambda item: None
        entry.PronunciationsOS = pron_seq

        with pytest.raises(mod.FP_DeduplicationError):
            ops._LexEntryOperations__DeduplicatePronunciationsInEntry(entry)

    def test_attribute_error_from_remove_propagates(self, monkeypatch, mock_flex_project):
        """
        The narrowed inner except must let AttributeError propagate
        (not log-and-swallow) -- this is exactly the exception class
        `dupe.OwningList.Remove(dupe)` raised under the pre-fix code.
        """
        ops, _mod = self._make_ops(monkeypatch, mock_flex_project)

        master = MockLCMObject(hvo=100)
        master.Form = MockMultiString({1: "apple"})
        dupe = MockLCMObject(hvo=101)
        dupe.Form = MockMultiString({1: "apple"})

        entry = MockLCMObject(hvo=1000)
        pron_seq = MockOwningSequence([master, dupe])

        def _raise_attribute_error(item):
            raise AttributeError("'ILexPronunciation' object has no attribute 'OwningList'")

        pron_seq.Remove = _raise_attribute_error
        entry.PronunciationsOS = pron_seq

        with pytest.raises(AttributeError):
            ops._LexEntryOperations__DeduplicatePronunciationsInEntry(entry)


# ===========================================================================
# Issue #318b -- Allomorph dedup (LexEntryOperations)
# ===========================================================================


class TestDeduplicateAllomorphsInEntry:
    def _make_ops(self, monkeypatch, mock_flex_project):
        from flexicon.code.Lexicon import LexEntryOperations as mod

        monkeypatch.setattr(mod, "ITsString", _IdentityITsString())
        _wire_writing_systems(mock_flex_project, handles=[1])
        return mod.LexEntryOperations(mock_flex_project), mod

    def test_duplicate_allomorph_is_actually_removed(self, monkeypatch, mock_flex_project):
        ops, _mod = self._make_ops(monkeypatch, mock_flex_project)

        master = MockLCMObject(hvo=200)
        master.Form = MockMultiString({1: "run"})
        master.MorphTypeRA = None
        dupe = MockLCMObject(hvo=201)
        dupe.Form = MockMultiString({1: "run"})
        dupe.MorphTypeRA = None

        entry = MockLCMObject(hvo=1000)
        entry.AlternateFormsOS = MockOwningSequence([master, dupe])

        assert len(list(entry.AlternateFormsOS)) == 2

        ops._LexEntryOperations__DeduplicateAllomorphsInEntry(entry)

        after = list(entry.AlternateFormsOS)
        assert len(after) == 1, (
            "Duplicate allomorph was not removed -- AlternateFormsOS "
            "length is unchanged, the exact silent-no-op shape of #318."
        )
        assert after[0].Hvo == master.Hvo

    def test_removal_that_silently_fails_raises_fp_deduplication_error(
        self, monkeypatch, mock_flex_project
    ):
        ops, mod = self._make_ops(monkeypatch, mock_flex_project)

        master = MockLCMObject(hvo=200)
        master.Form = MockMultiString({1: "run"})
        master.MorphTypeRA = None
        dupe = MockLCMObject(hvo=201)
        dupe.Form = MockMultiString({1: "run"})
        dupe.MorphTypeRA = None

        entry = MockLCMObject(hvo=1000)
        allomorph_seq = MockOwningSequence([master, dupe])

        allomorph_seq.Remove = lambda item: None
        entry.AlternateFormsOS = allomorph_seq

        with pytest.raises(mod.FP_DeduplicationError):
            ops._LexEntryOperations__DeduplicateAllomorphsInEntry(entry)


# ===========================================================================
# Issue #318c -- Example dedup (LexSenseOperations)
# ===========================================================================


class TestDeduplicateExamplesInSense:
    def _make_ops(self, mock_flex_project):
        from flexicon.code.Lexicon import LexSenseOperations as mod

        return mod.LexSenseOperations(mock_flex_project), mod

    def test_duplicate_example_is_actually_removed(self, mock_flex_project):
        ops, mod = self._make_ops(mock_flex_project)

        master = MockLCMObject(hvo=300)
        dupe = MockLCMObject(hvo=301)

        sense = MockLCMObject(hvo=2000)
        sense.ExamplesOS = MockOwningSequence([master, dupe])

        # __FindDuplicateExamplesInSense does its own text/reference
        # comparison; stub it directly so this test targets only the
        # removal logic under test (the OwningList -> ExamplesOS fix),
        # matching the ticket's instruction to test the Remove() site.
        ops._LexSenseOperations__FindDuplicateExamplesInSense = Mock(return_value=[(master, [dupe])])

        assert len(list(sense.ExamplesOS)) == 2

        ops._LexSenseOperations__DeduplicateExamplesInSense(sense)

        after = list(sense.ExamplesOS)
        assert len(after) == 1, (
            "Duplicate example was not removed -- ExamplesOS length is "
            "unchanged, the exact silent-no-op shape of #318."
        )
        assert after[0].Hvo == master.Hvo

    def test_removal_that_silently_fails_raises_fp_deduplication_error(self, mock_flex_project):
        ops, mod = self._make_ops(mock_flex_project)

        master = MockLCMObject(hvo=300)
        dupe = MockLCMObject(hvo=301)

        sense = MockLCMObject(hvo=2000)
        example_seq = MockOwningSequence([master, dupe])

        example_seq.Remove = lambda item: None
        sense.ExamplesOS = example_seq

        ops._LexSenseOperations__FindDuplicateExamplesInSense = Mock(return_value=[(master, [dupe])])

        with pytest.raises(mod.FP_DeduplicationError):
            ops._LexSenseOperations__DeduplicateExamplesInSense(sense)

    def test_no_duplicates_does_not_raise(self, mock_flex_project):
        ops, mod = self._make_ops(mock_flex_project)

        e1 = MockLCMObject(hvo=300)
        e2 = MockLCMObject(hvo=301)

        sense = MockLCMObject(hvo=2000)
        sense.ExamplesOS = MockOwningSequence([e1, e2])

        ops._LexSenseOperations__FindDuplicateExamplesInSense = Mock(return_value=[])

        ops._LexSenseOperations__DeduplicateExamplesInSense(sense)

        assert len(list(sense.ExamplesOS)) == 2


# ===========================================================================
# Source-level ratchet: guards against reintroducing dupe.OwningList
# ===========================================================================


def test_pronunciation_dedup_does_not_read_owninglist():
    import inspect

    from flexicon.code.Lexicon.LexEntryOperations import LexEntryOperations

    source = inspect.getsource(
        LexEntryOperations._LexEntryOperations__DeduplicatePronunciationsInEntry
    )
    assert "dupe.OwningList.Remove" not in source, (
        "__DeduplicatePronunciationsInEntry reads dupe.OwningList again -- "
        "that property does not exist on ILexPronunciation (issue #318)."
    )
    assert "entry.PronunciationsOS.Remove" in source


def test_allomorph_dedup_does_not_read_owninglist():
    import inspect

    from flexicon.code.Lexicon.LexEntryOperations import LexEntryOperations

    source = inspect.getsource(LexEntryOperations._LexEntryOperations__DeduplicateAllomorphsInEntry)
    assert "dupe.OwningList.Remove" not in source
    assert "entry.AlternateFormsOS.Remove" in source


def test_example_dedup_does_not_read_owninglist():
    import inspect

    from flexicon.code.Lexicon.LexSenseOperations import LexSenseOperations

    source = inspect.getsource(LexSenseOperations._LexSenseOperations__DeduplicateExamplesInSense)
    assert "dupe.OwningList.Remove" not in source
    assert "sense.ExamplesOS.Remove" in source
