#
#   test_issue599_allomorph_getform_affix_offline.py
#
#   Offline regression lock for issue #599: the shared resolver
#   AllomorphOperations.__GetAllomorphObject must dispatch on ClassName so
#   affix allomorphs are never cast to IMoStemAllomorph (and vice versa),
#   and must unwrap GetAll() wrappers before casting.
#
#   Copyright 2026
#

import pathlib
from unittest.mock import MagicMock

import pytest

from flexicon.code.Lexicon import AllomorphOperations as mod

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
LIVE_GATE = REPO_ROOT / "tests" / "operations" / "test_issue599_allomorph_getform_affix_live.py"


class _FakeLcm:
    def __init__(self, class_name):
        self.ClassName = class_name


def _make_ops(monkeypatch):
    stem_cast = MagicMock(name="IMoStemAllomorph")
    affix_cast = MagicMock(name="IMoAffixAllomorph")
    monkeypatch.setattr(mod, "IMoStemAllomorph", stem_cast)
    monkeypatch.setattr(mod, "IMoAffixAllomorph", affix_cast)
    project = MagicMock()
    ops = mod.AllomorphOperations(project)
    return ops, project, stem_cast, affix_cast


class TestIssue599ResolverDispatch:
    def test_affix_object_is_cast_to_affix_not_stem(self, monkeypatch):
        ops, _, stem_cast, affix_cast = _make_ops(monkeypatch)
        obj = _FakeLcm("MoAffixAllomorph")
        resolved = ops._AllomorphOperations__GetAllomorphObject(obj)
        affix_cast.assert_called_once_with(obj)
        stem_cast.assert_not_called()
        assert resolved is affix_cast.return_value

    def test_stem_object_is_cast_to_stem_not_affix(self, monkeypatch):
        ops, _, stem_cast, affix_cast = _make_ops(monkeypatch)
        obj = _FakeLcm("MoStemAllomorph")
        resolved = ops._AllomorphOperations__GetAllomorphObject(obj)
        stem_cast.assert_called_once_with(obj)
        affix_cast.assert_not_called()
        assert resolved is stem_cast.return_value

    def test_affix_hvo_is_cast_to_affix(self, monkeypatch):
        ops, project, stem_cast, affix_cast = _make_ops(monkeypatch)
        obj = _FakeLcm("MoAffixAllomorph")
        project.Object.return_value = obj
        ops._AllomorphOperations__GetAllomorphObject(1234)
        project.Object.assert_called_once_with(1234)
        affix_cast.assert_called_once_with(obj)
        stem_cast.assert_not_called()

    def test_wrapper_is_unwrapped_before_cast(self, monkeypatch):
        ops, _, stem_cast, affix_cast = _make_ops(monkeypatch)
        raw = _FakeLcm("MoAffixAllomorph")
        wrapper = MagicMock()
        wrapper.lcm_object = raw
        ops._AllomorphOperations__GetAllomorphObject(wrapper)
        affix_cast.assert_called_once_with(raw)
        stem_cast.assert_not_called()

    def test_unrecognized_class_returned_unchanged_never_raises(self, monkeypatch):
        ops, _, stem_cast, affix_cast = _make_ops(monkeypatch)
        obj = _FakeLcm("LexSense")
        assert ops._AllomorphOperations__GetAllomorphObject(obj) is obj
        stem_cast.assert_not_called()
        affix_cast.assert_not_called()


def test_issue599_live_gate_module_exists():
    text = LIVE_GATE.read_text(encoding="utf-8")
    assert "MoAffixAllomorph" in text and "GetForm" in text
    assert "requires_live_project" in text
