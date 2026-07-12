#
#   test_wrap_enumerable_pattern.py
#
#   Class: TestNeedsEnumerableWrap / TestGetAllSiblingSites
#          Regression coverage for issue #201: GetAll()/GetAnalyses()-style
#          methods returned a bare LCM iterator/generator that was not
#          subscriptable and had no len(), so `entries[0]` and `len(entries)`
#          raised TypeError.
#
#   Bug class (closes #201):
#     - `wrap_enumerable` only re-wrapped results exposing `GetEnumerator`
#       (a raw C# IEnumerable). Two common return shapes slipped past that
#       check untouched:
#         1. `self.project.ObjectsIn(...)`, which already calls Python's
#            `iter()` on the underlying C# enumerable -- the result exposes
#            `__next__`/`__iter__` but not `GetEnumerator`.
#         2. Generator-function method bodies (`yield ...`), which return a
#            plain Python generator object -- also has `__next__` but no
#            `GetEnumerator`, and is not subscriptable / has no len().
#
#   The fix widens `wrap_enumerable`'s detection (via the new
#   `_needs_enumerable_wrap` helper in BaseOperations.py) to catch any
#   plain iterator/generator that doesn't already behave like a sequence,
#   and wraps it in the existing `EnumerableWrapper` (lazy: materializes
#   into a list only on first `len()`/index/iteration access). This file
#   locks the PATTERN, not just the originally-reported
#   `LexEntryOperations.GetAll` instance:
#
#     1. Unit tests against `_needs_enumerable_wrap` / `wrap_enumerable`
#        directly, covering both broken shapes plus already-fine shapes
#        (lists, existing wrappers) that must NOT be re-wrapped.
#     2. Mock-based regression tests for each of the sibling call sites
#        confirmed affected: LexEntryOperations.GetAll,
#        TextOperations.GetAll, SegmentOperations.GetAll (paragraph
#        segments -- a generator-based sibling of the reported
#        SegmentOperations.GetAnalyses), and a guard test proving
#        SegmentOperations.GetAnalyses already returned a real list (no
#        behavior change needed there).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import os
import sys
from unittest.mock import Mock, patch

import pytest

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_test_dir)
sys.path.insert(0, _project_root)

from flexicon.code.BaseOperations import (
    EnumerableWrapper,
    _needs_enumerable_wrap,
    wrap_enumerable,
    OperationsMethod,
)

from tests.operations import mock_flex_project, MockLCMObject  # noqa: F401


# =============================================================================
# UNIT TESTS: _needs_enumerable_wrap / wrap_enumerable / EnumerableWrapper
# =============================================================================


class TestNeedsEnumerableWrap:
    """Direct unit tests for the detection helper (the actual bug fix)."""

    def test_none_is_not_wrapped(self):
        assert _needs_enumerable_wrap(None) is False

    def test_list_is_not_wrapped(self):
        """Already a real list: len()/indexing already work, leave it alone."""
        assert _needs_enumerable_wrap([1, 2, 3]) is False

    def test_tuple_is_not_wrapped(self):
        assert _needs_enumerable_wrap((1, 2, 3)) is False

    def test_existing_enumerable_wrapper_is_not_rewrapped(self):
        wrapper = EnumerableWrapper([1, 2, 3])
        assert _needs_enumerable_wrap(wrapper) is False

    def test_raw_dotnet_style_enumerable_is_wrapped(self):
        """Simulates a raw C# IEnumerable (exposes GetEnumerator)."""
        fake_dotnet_enumerable = Mock(spec=["GetEnumerator"])
        assert _needs_enumerable_wrap(fake_dotnet_enumerable) is True

    def test_plain_python_iterator_is_wrapped(self):
        """
        Reproduces the exact issue #201 shape: `self.project.ObjectsIn(...)`
        returns `iter(repo.AllInstances())` -- a plain Python iterator with
        __next__ but no GetEnumerator, no __len__, no __getitem__.
        """
        plain_iterator = iter([1, 2, 3])
        assert _needs_enumerable_wrap(plain_iterator) is True

    def test_generator_is_wrapped(self):
        """
        Reproduces the generator-function shape used by many GetAll()
        implementations (`yield` instead of `return`).
        """
        def gen():
            yield 1
            yield 2

        assert _needs_enumerable_wrap(gen()) is True

    def test_sequence_like_object_is_not_rewrapped(self):
        """
        An object that already supports both __len__ and __getitem__
        (e.g. a SmartCollection subclass) must be left alone.
        """
        class FakeSequence:
            def __len__(self):
                return 0

            def __getitem__(self, index):
                raise IndexError

        assert _needs_enumerable_wrap(FakeSequence()) is False


class TestWrapEnumerableDecorator:
    """Integration test of the decorator stack as used throughout Operations classes."""

    def _make_ops_class(self, return_value_factory):
        class FakeOperations:
            @wrap_enumerable
            @OperationsMethod
            def GetAll(self):
                return return_value_factory()

        return FakeOperations

    def test_generator_returning_method_is_subscriptable_and_lenable(self):
        items = [MockLCMObject(hvo=i) for i in range(3)]

        def make_generator():
            def gen():
                for item in items:
                    yield item
            return gen()

        cls = self._make_ops_class(make_generator)
        result = cls().GetAll()

        assert len(result) == 3
        assert result[0].Hvo == items[0].Hvo
        assert result[-1].Hvo == items[-1].Hvo
        # Re-iterating must not exhaust/empty the wrapper.
        assert list(result) == list(result) == items

    def test_iter_wrapped_ObjectsIn_style_result_is_subscriptable_and_lenable(self):
        items = [MockLCMObject(hvo=i) for i in range(3)]

        cls = self._make_ops_class(lambda: iter(items))
        result = cls().GetAll()

        assert len(result) == 3
        assert result[0].Hvo == items[0].Hvo

    def test_list_returning_method_passes_through_unchanged(self):
        items = [1, 2, 3]
        cls = self._make_ops_class(lambda: items)
        result = cls().GetAll()

        # No wrapping needed/performed: identity preserved.
        assert result is items


# =============================================================================
# SIBLING-SITE REGRESSION TESTS (mock-based, no live FLEx project required)
# =============================================================================


class TestLexEntryOperationsGetAllPattern:
    def test_getall_not_bare_iterator(self, mock_flex_project):
        from flexicon.code.Lexicon.LexEntryOperations import LexEntryOperations

        entries = [MockLCMObject(hvo=i) for i in range(3)]
        with patch.object(mock_flex_project, "ObjectsIn", return_value=iter(entries)):
            ops = LexEntryOperations(mock_flex_project)
            result = ops.GetAll()
            assert len(result) == 3
            assert result[0].Hvo == entries[0].Hvo


class TestTextOperationsGetAllPattern:
    def test_getall_not_bare_iterator(self, mock_flex_project):
        from flexicon.code.TextsWords.TextOperations import TextOperations

        texts = [MockLCMObject(hvo=100 + i) for i in range(2)]
        with patch.object(mock_flex_project, "ObjectsIn", return_value=iter(texts)):
            ops = TextOperations(mock_flex_project)
            result = ops.GetAll()
            assert len(result) == 2
            assert result[0].Hvo == texts[0].Hvo


class TestSegmentOperationsGetAllPattern:
    """
    SegmentOperations.GetAll(paragraph) is a `yield`-based sibling of the
    originally reported SegmentOperations.GetAnalyses. It is fixed by the
    same central `wrap_enumerable` change.
    """

    def test_getall_not_bare_generator(self, mock_flex_project):
        from flexicon.code.TextsWords.SegmentOperations import SegmentOperations

        segments = [MockLCMObject(hvo=200 + i) for i in range(4)]
        mock_paragraph = Mock()
        mock_paragraph.SegmentsOS = segments

        ops = SegmentOperations(mock_flex_project)
        result = ops.GetAll(mock_paragraph)

        assert len(result) == 4
        assert result[0].Hvo == segments[0].Hvo
        assert result[-1].Hvo == segments[-1].Hvo


class TestSegmentOperationsGetAnalysesGuard:
    """
    Guard test: SegmentOperations.GetAnalyses already returns a real
    `list(...)`, so it was never actually affected by the bare-iterator
    bug at the current code revision. This locks that behavior so a
    future refactor doesn't reintroduce the #201 pattern here.
    """

    def test_getanalyses_returns_real_list(self, mock_flex_project):
        from flexicon.code.TextsWords.SegmentOperations import SegmentOperations

        analyses = [MockLCMObject(hvo=300 + i) for i in range(2)]
        mock_segment = Mock()
        mock_segment.AnalysesRS = analyses

        ops = SegmentOperations(mock_flex_project)
        result = ops.GetAnalyses(mock_segment)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].Hvo == analyses[0].Hvo
