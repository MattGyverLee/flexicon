#
#   test_issue546_allomorph_isabstract_offline.py
#
#   Offline coverage for issue #546: AllomorphOperations.GetIsAbstract /
#   SetIsAbstract, including the lexeme-form path.
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import contextlib

import pytest

from flexicon.code.FLExProject import (
    FP_NullParameterError,
    FP_ParameterError,
    FP_ReadOnlyError,
)
from flexicon.code.Lexicon.AllomorphOperations import AllomorphOperations


class _FakeProject:
    """Minimal project stub: only writeEnabled is consulted."""

    def __init__(self, write_enabled=True):
        self.writeEnabled = write_enabled


class _FakeAllomorph:
    """Minimal IMoForm stub carrying only IsAbstract."""

    ClassName = "MoStemAllomorph"

    def __init__(self, is_abstract=False):
        self.IsAbstract = is_abstract


def _ops_for(fake_allomorph, write_enabled=True, seen=None):
    """AllomorphOperations bound to a fake project, resolver stubbed."""
    ops = AllomorphOperations(_FakeProject(write_enabled))
    if seen is not None:
        orig = seen
    else:
        orig = []

    def _resolve(item):
        orig.append(item)
        return fake_allomorph

    ops._AllomorphOperations__GetAllomorphObject = _resolve
    ops._TransactionCM = lambda label: contextlib.nullcontext()
    return ops


class TestGetIsAbstract:
    def test_returns_bool_value(self):
        ops = _ops_for(_FakeAllomorph(True))
        assert ops.GetIsAbstract(object()) is True

        ops = _ops_for(_FakeAllomorph(False))
        assert ops.GetIsAbstract(object()) is False

    def test_routes_through_shared_resolver(self):
        seen = []
        sentinel = object()
        ops = _ops_for(_FakeAllomorph(False), seen=seen)
        ops.GetIsAbstract(sentinel)
        assert seen == [sentinel]

    def test_accepts_lexeme_form_object(self):
        """No AlternateFormsOS membership check: a lexeme form resolves."""
        seen = []
        lexeme = _FakeAllomorph(False)
        ops = _ops_for(lexeme, seen=seen)
        assert ops.GetIsAbstract(lexeme) is False
        assert seen == [lexeme]

    def test_none_rejected(self):
        ops = _ops_for(_FakeAllomorph(False))
        with pytest.raises((FP_NullParameterError, FP_ParameterError, ValueError)):
            ops.GetIsAbstract(None)


class TestSetIsAbstract:
    def test_sets_flag_and_coerces_to_bool(self):
        allo = _FakeAllomorph(False)
        ops = _ops_for(allo)
        ops.SetIsAbstract(object(), True)
        assert allo.IsAbstract is True

        ops.SetIsAbstract(object(), 0)
        assert allo.IsAbstract is False

    def test_routes_through_shared_resolver(self):
        seen = []
        sentinel = object()
        ops = _ops_for(_FakeAllomorph(False), seen=seen)
        ops.SetIsAbstract(sentinel, True)
        assert seen == [sentinel]

    def test_accepts_lexeme_form_object(self):
        seen = []
        lexeme = _FakeAllomorph(False)
        ops = _ops_for(lexeme, seen=seen)
        ops.SetIsAbstract(lexeme, True)
        assert lexeme.IsAbstract is True
        assert seen == [lexeme]

    def test_read_only_rejected(self):
        ops = _ops_for(_FakeAllomorph(False), write_enabled=False)
        with pytest.raises((FP_ReadOnlyError, Exception)):
            ops.SetIsAbstract(object(), True)

    def test_none_allomorph_rejected(self):
        ops = _ops_for(_FakeAllomorph(False))
        with pytest.raises((FP_NullParameterError, FP_ParameterError, ValueError)):
            ops.SetIsAbstract(None, True)

    def test_none_value_rejected(self):
        ops = _ops_for(_FakeAllomorph(False))
        with pytest.raises((FP_NullParameterError, FP_ParameterError, ValueError)):
            ops.SetIsAbstract(object(), None)


class TestDuplicatePreservesIsAbstract:
    def test_duplicate_copies_isabstract_in_source(self):
        import inspect

        dup = AllomorphOperations.__dict__["Duplicate"]
        while hasattr(dup, "func"):
            dup = dup.func
        src = inspect.getsource(dup)
        assert "IsAbstract" in src, (
            "Duplicate must copy IsAbstract so a duplicate of an abstract "
            "form stays abstract (issue #546)."
        )
