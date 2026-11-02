#
#   test_issue782_wfianalysis_exists_offline.py
#
#   Offline regression for issue #782: WfiAnalysisOperations.Exists returns
#   False (not an exception) for a stale or unknown analysis HVO.
#
#   Copyright 2026
#

from types import SimpleNamespace

import pytest

from flexicon.code.FLExProject import FP_ParameterError
from flexicon.code.TextsWords.WfiAnalysisOperations import WfiAnalysisOperations


class _StubProject:
    def __init__(self, resolver):
        self._resolver = resolver
        self.calls = []

    def Object(self, hvo):
        self.calls.append(hvo)
        return self._resolver(hvo)


def _make_ops(project, wordform):
    ops = object.__new__(WfiAnalysisOperations)
    ops.project = project
    # Bypass wordform casting (needs a real LCM object); not under test.
    ops._WfiAnalysisOperations__GetWordformObject = lambda wf: wordform
    return ops


def _stale(hvo):
    raise FP_ParameterError("Object not found")


def test_issue782_exists_false_for_stale_hvo():
    wordform = SimpleNamespace(AnalysesOC=[SimpleNamespace(Hvo=1)])
    project = _StubProject(_stale)
    ops = _make_ops(project, wordform)
    assert ops.Exists(100, 999999) is False
    assert project.calls == [999999]


def test_issue782_exists_false_for_wordform_without_analyses():
    wordform = SimpleNamespace(AnalysesOC=[])
    ops = _make_ops(_StubProject(_stale), wordform)
    assert ops.Exists(100, 5) is False


def test_issue782_exists_only_guards_resolution_failure():
    # A non-FP_ParameterError from Object() must not be swallowed as False.
    def boom(hvo):
        raise RuntimeError("unexpected")

    ops = _make_ops(
        _StubProject(boom), SimpleNamespace(AnalysesOC=[SimpleNamespace(Hvo=1)])
    )
    with pytest.raises(Exception) as ei:
        ops.Exists(100, 1)
    assert not isinstance(ei.value, FP_ParameterError) or "unexpected" in str(ei.value)
