"""
Offline tests for issue 631: inflection classes live under POS
(InflectionClassesOC / SubclassesOC), never in ProdRestrictOA; exception
features are the ProdRestrictOA items.
"""

import contextlib
from types import SimpleNamespace
from unittest.mock import Mock, MagicMock, patch

import pytest

from flexicon.code.Grammar.InflectionFeatureOperations import InflectionFeatureOperations
from flexicon.code.FLExProject import FP_ParameterError, FP_ReadOnlyError

MOD = "flexicon.code.Grammar.InflectionFeatureOperations"


class _OC(list):
    """List with the LCM collection Add/Remove surface."""

    def Add(self, x):
        self.append(x)

    def Remove(self, x):
        self.remove(x)


def _ic(name, subs=()):
    return SimpleNamespace(Hvo=id(name), Name=name, SubclassesOC=_OC(subs), ClassName="MoInflClass")


def _pos(inflclasses=()):
    return SimpleNamespace(InflectionClassesOC=_OC(inflclasses), ClassName="PartOfSpeech")


def _flatten(ocs):
    out = []
    for ic in ocs:
        out.append(ic)
        out.extend(_flatten(ic.SubclassesOC))
    return out


def _ops(write=True, pos_list=(), prod_restrict=None):
    project = Mock()
    project.writeEnabled = write
    project._undoable = False
    project.Transaction = Mock(side_effect=lambda label="t": contextlib.nullcontext())
    project.UndoableOperation = Mock(side_effect=lambda label: contextlib.nullcontext())
    project.project.DefaultAnalWs = 2
    project._FLExProject__WSHandle = Mock(side_effect=lambda ws, d: ws if ws is not None else d)
    posops = Mock()
    posops.GetAll = Mock(return_value=list(pos_list))
    posops.GetInflectionClasses = Mock(
        side_effect=lambda p, recursive=False: _flatten(p.InflectionClassesOC)
    )
    project.POS = posops
    project.lp.MorphologicalDataOA = SimpleNamespace(ProdRestrictOA=prod_restrict)
    return InflectionFeatureOperations(project), project


@pytest.fixture
def lcm_stubs():
    ts = MagicMock()
    ts.MakeString = Mock(side_effect=lambda t, ws: SimpleNamespace(Text=t))
    with patch(f"{MOD}.IMoInflClass", side_effect=lambda x: x), \
            patch(f"{MOD}.ICmPossibility", side_effect=lambda x: x), \
            patch(f"{MOD}.ITsString", side_effect=lambda x: x), \
            patch(f"{MOD}.cast_to_concrete", side_effect=lambda x: x), \
            patch(f"{MOD}.require_lcm_object", side_effect=lambda x, *a: x), \
            patch(f"{MOD}.TsStringUtils", new=ts):
        yield


class _FakeName:
    """IMultiUnicode stand-in: get_String returns an object with .Text."""

    def __init__(self, text=""):
        self.text = text

    def get_String(self, ws):
        return SimpleNamespace(Text=self.text)

    def set_String(self, ws, ts):
        self.text = ts.Text


class TestInflectionClassGetAll:
    def test_walks_pos_and_subclasses(self, lcm_stubs):
        sub = _ic("sub")
        top = _ic("top", [sub])
        ops, _ = _ops(pos_list=[_pos([top]), _pos([_ic("other")])])
        names = [i.Name for i in ops.InflectionClassGetAll()]
        assert names == ["top", "sub", "other"]

    def test_ignores_prod_restrict_exception_features(self, lcm_stubs):
        pr = SimpleNamespace(PossibilitiesOS=_OC([SimpleNamespace()]))
        ops, _ = _ops(pos_list=[_pos([_ic("a")])], prod_restrict=pr)
        assert [i.Name for i in ops.InflectionClassGetAll()] == ["a"]


class TestInflectionClassCreate:
    def _factory(self, project):
        def make():
            ic = SimpleNamespace(SubclassesOC=_OC(), Name=_FakeName())
            return ic

        f = Mock()
        f.Create = Mock(side_effect=make)
        project.project.ServiceLocator.GetService = Mock(return_value=f)

    def test_name_only_raises_pos_required(self, lcm_stubs):
        ops, _ = _ops()
        with pytest.raises(FP_ParameterError, match="part of speech"):
            ops.InflectionClassCreate("X")

    def test_neither_given_error_names_both_options(self, lcm_stubs):
        ops, _ = _ops()
        with pytest.raises(FP_ParameterError) as excinfo:
            ops.InflectionClassCreate("X")
        msg = str(excinfo.value)
        assert "pos=" in msg and "parent=" in msg

    def test_pos_and_parent_mismatch_warns_and_parent_wins(self, lcm_stubs, caplog):
        ops, project = _ops()
        self._factory(project)
        real_pos = _pos()
        real_pos.Hvo = 1
        other_pos = _pos()
        other_pos.Hvo = 2
        parent = _ic("P")
        parent.Name = _FakeName("P")
        parent.Owner = real_pos
        with caplog.at_level("WARNING"):
            ic = ops.InflectionClassCreate("Kid", pos=other_pos, parent=parent)
        assert list(parent.SubclassesOC) == [ic]
        assert list(other_pos.InflectionClassesOC) == []
        msgs = [r.getMessage() for r in caplog.records]
        assert any("pos=2" in m and "parent=" in m for m in msgs)

    def test_pos_and_parent_consistent_does_not_warn(self, lcm_stubs, caplog):
        ops, project = _ops()
        self._factory(project)
        pos = _pos()
        pos.Hvo = 1
        parent = _ic("P")
        parent.Name = _FakeName("P")
        parent.Owner = pos
        with caplog.at_level("WARNING"):
            ops.InflectionClassCreate("Kid", pos=pos, parent=parent)
        assert not [r for r in caplog.records if r.levelname == "WARNING"]

    def test_read_only_raises(self, lcm_stubs):
        ops, _ = _ops(write=False)
        with pytest.raises(FP_ReadOnlyError):
            ops.InflectionClassCreate("X", pos=_pos())

    def test_under_pos(self, lcm_stubs):
        ops, project = _ops()
        self._factory(project)
        pos = _pos()
        ic = ops.InflectionClassCreate("Decl", pos=pos)
        assert list(pos.InflectionClassesOC) == [ic]
        assert ic.Name.text == "Decl"

    def test_under_parent_never_touches_prod_restrict(self, lcm_stubs):
        pr = SimpleNamespace(PossibilitiesOS=_OC())
        ops, project = _ops(prod_restrict=pr)
        self._factory(project)
        parent = _ic("P")
        parent.Name = _FakeName("P")
        ic = ops.InflectionClassCreate("Kid", parent=parent)
        assert list(parent.SubclassesOC) == [ic]
        assert len(pr.PossibilitiesOS) == 0

    def test_duplicate_sibling_rejected(self, lcm_stubs):
        ops, project = _ops()
        self._factory(project)
        existing = _ic("x")
        existing.Name = _FakeName("Decl")
        pos = _pos([existing])
        with pytest.raises(FP_ParameterError, match="already exists"):
            ops.InflectionClassCreate("decl", pos=pos)


class TestInflectionClassDelete:
    def test_deletes_from_pos(self, lcm_stubs):
        ops, _ = _ops()
        ic = _ic("a")
        pos = _pos([ic])
        ic.Owner = pos
        ops.InflectionClassDelete(ic)
        assert list(pos.InflectionClassesOC) == []

    def test_deletes_from_parent_class(self, lcm_stubs):
        ops, _ = _ops()
        kid = _ic("k")
        parent = _ic("p", [kid])
        kid.Owner = parent
        ops.InflectionClassDelete(kid)
        assert list(parent.SubclassesOC) == []


class TestExceptionFeatures:
    def test_get_all_empty_when_list_missing(self, lcm_stubs):
        ops, _ = _ops()
        assert list(ops.ExceptionFeatureGetAll()) == []

    def test_create_makes_list_when_missing(self, lcm_stubs):
        ops, project = _ops()
        created_list = SimpleNamespace(PossibilitiesOS=_OC())
        fac = Mock()
        fac.Create = Mock(
            side_effect=lambda: SimpleNamespace(Name=_FakeName(), Abbreviation=_FakeName())
        )
        listfac = Mock()
        listfac.Create = Mock(return_value=created_list)
        list_key, item_key = object(), object()

        with patch(f"{MOD}.ICmPossibilityListFactory", new=list_key), \
                patch(f"{MOD}.ICmPossibilityFactory", new=item_key):
            project.project.ServiceLocator.GetService = Mock(
                side_effect=lambda t: listfac if t is list_key else fac
            )
            ef = ops.ExceptionFeatureCreate("Irr", "irr")
        md = project.lp.MorphologicalDataOA
        assert md.ProdRestrictOA is created_list
        assert list(created_list.PossibilitiesOS) == [ef]
        assert ef.Name.text == "Irr"
        assert ef.Abbreviation.text == "irr"

    def test_find_by_name_case_insensitive(self, lcm_stubs):
        pr = SimpleNamespace(PossibilitiesOS=_OC())
        for n in ("Alpha", "Beta"):
            pr.PossibilitiesOS.append(SimpleNamespace(Name=_FakeName(n)))
        ops, _ = _ops(prod_restrict=pr)
        assert ops.ExceptionFeatureFind("beta") is pr.PossibilitiesOS[1]
        assert ops.ExceptionFeatureFind("gamma") is None
