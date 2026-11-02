#
#   test_issue830_allomorph_inflection_class_offline.py
#
#   Offline (mock) tests for issue #830: Get/Add/RemoveInflectionClass act on
#   IMoAffixForm.InflectionClassesRC (MoAffixAllomorph / MoAffixProcess),
#   not on stem allomorphs.
#
#   Copyright 2026
#

import contextlib
from types import SimpleNamespace

import pytest

from flexicon.code.Lexicon import AllomorphOperations as mod
from flexicon.code.FLExProject import FP_ParameterError


class _RC(list):
    """Reference-collection stand-in (Add/Remove, HVO-based removal)."""

    def Add(self, item):
        self.append(item)

    def Remove(self, item):
        for i, member in enumerate(self):
            if member.Hvo == item.Hvo:
                del self[i]
                return
        raise ValueError("not in collection")


def _infl(hvo):
    return SimpleNamespace(ClassName="MoInflClass", Hvo=hvo)


def _allo(class_name, hvo=201, classes=()):
    return SimpleNamespace(ClassName=class_name, Hvo=hvo, InflectionClassesRC=_RC(classes))


@pytest.fixture
def ops(monkeypatch):
    identity = lambda x: x  # noqa: E731
    for name in ("IMoStemAllomorph", "IMoAffixAllomorph", "IMoAffixForm"):
        monkeypatch.setattr(mod, name, identity)
    monkeypatch.setattr(mod, "cast_to_concrete", identity)
    project = SimpleNamespace(writeEnabled=True)
    project.Object = lambda hvo: project._objs[hvo]
    project._objs = {}
    o = mod.AllomorphOperations(project)
    labels = []

    @contextlib.contextmanager
    def _cm(label):
        labels.append(label)
        yield

    monkeypatch.setattr(o, "_TransactionCM", _cm)
    o.labels = labels
    o.fake_project = project
    return o


@pytest.mark.parametrize("class_name", ["MoAffixAllomorph", "MoAffixProcess"])
class TestAffixForms:
    def test_add_get_remove(self, ops, class_name):
        allo = _allo(class_name)
        ic = _infl(901)
        ops.AddInflectionClass(allo, ic)
        assert [c.Hvo for c in ops.GetInflectionClasses(allo)] == [901]
        assert [c.Hvo for c in allo.InflectionClassesRC] == [901]
        ops.RemoveInflectionClass(allo, ic)
        assert ops.GetInflectionClasses(allo) == []
        assert ops.labels == ["Add inflection class", "Remove inflection class"]

    def test_add_is_idempotent_and_opens_no_undo_task(self, ops, class_name):
        allo = _allo(class_name)
        ops.AddInflectionClass(allo, _infl(901))
        ops.AddInflectionClass(allo, _infl(901))  # distinct object, same HVO
        assert len(allo.InflectionClassesRC) == 1
        assert ops.labels == ["Add inflection class"]

    def test_remove_missing_is_noop(self, ops, class_name):
        allo = _allo(class_name, classes=[_infl(901)])
        ops.RemoveInflectionClass(allo, _infl(902))
        assert len(allo.InflectionClassesRC) == 1
        assert ops.labels == []

    def test_remove_matches_by_hvo(self, ops, class_name):
        allo = _allo(class_name, classes=[_infl(901), _infl(902)])
        ops.RemoveInflectionClass(allo, _infl(901))
        assert [c.Hvo for c in allo.InflectionClassesRC] == [902]

    def test_hvo_inputs(self, ops, class_name):
        allo = _allo(class_name, hvo=201)
        ic = _infl(901)
        ops.fake_project._objs.update({201: allo, 901: ic})
        ops.AddInflectionClass(201, 901)
        assert [c.Hvo for c in ops.GetInflectionClasses(201)] == [901]


class TestStemAllomorph:
    def test_get_returns_empty(self, ops):
        stem = _allo("MoStemAllomorph")
        assert ops.GetInflectionClasses(stem) == []

    def test_add_raises_and_names_msa_route(self, ops):
        stem = _allo("MoStemAllomorph")
        with pytest.raises(FP_ParameterError, match="SetInflectionClass"):
            ops.AddInflectionClass(stem, _infl(901))
        assert len(stem.InflectionClassesRC) == 0
        assert ops.labels == []

    def test_remove_raises_and_names_msa_route(self, ops):
        stem = _allo("MoStemAllomorph", classes=[_infl(901)])
        with pytest.raises(FP_ParameterError, match="SetInflectionClass"):
            ops.RemoveInflectionClass(stem, _infl(901))
        assert len(stem.InflectionClassesRC) == 1


class TestOtherClasses:
    def test_get_returns_empty_never_raises(self, ops):
        assert ops.GetInflectionClasses(_allo("LexEntry")) == []

    def test_add_remove_raise(self, ops):
        other = _allo("LexEntry")
        with pytest.raises(FP_ParameterError):
            ops.AddInflectionClass(other, _infl(901))
        with pytest.raises(FP_ParameterError):
            ops.RemoveInflectionClass(other, _infl(901))

    def test_non_infl_class_rejected(self, ops):
        allo = _allo("MoAffixAllomorph")
        with pytest.raises(FP_ParameterError):
            ops.AddInflectionClass(allo, SimpleNamespace(ClassName="PartOfSpeech", Hvo=5))
