#
#   test_issue472_possibility_reparent_offline.py
#
#   Offline coverage for issue #472: LocationOperations.SetRegion and
#   PublicationOperations.SetIsDefault must not Remove-then-Add on LCM
#   owning sequences (Remove deletes the ownee).
#
#   Platform: Python 3.8+
#   Copyright 2026
#

import ast
import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest


_STUB_PREFIXES = ("flexicon", "SIL", "System")


def _is_stubbed_name(name):
    return any(name == p or name.startswith(p + ".") for p in _STUB_PREFIXES)


@pytest.fixture(autouse=True)
def _restore_stubbed_sys_modules():
    """Undo the loader's sys.modules stubs after every test.

    The loaders below install stub ``flexicon`` / ``SIL`` / ``System``
    modules (no ``__file__``) directly into sys.modules. Leaving them in
    place poisoned every later test module that imports the real package
    ("unknown location" ImportErrors, stub BaseOperations leaking into
    other suites) -- same bug class as #476. The loaded module keeps its
    import-time bindings, so restoring afterwards is safe.
    """
    saved = {n: m for n, m in sys.modules.items() if _is_stubbed_name(n)}
    try:
        yield
    finally:
        for name in [n for n in sys.modules if _is_stubbed_name(n)]:
            if name not in saved:
                del sys.modules[name]
        for name, module in saved.items():
            if sys.modules.get(name) is not module:
                sys.modules[name] = module


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _stub_flexicon_packages():
    flexicon = types.ModuleType("flexicon")
    flexicon_code = types.ModuleType("flexicon.code")
    flexicon_flex = types.ModuleType("flexicon.code.FLExProject")
    flexicon_flex.FP_ParameterError = type("FP_ParameterError", (Exception,), {})
    flexicon_flex.FP_ReadOnlyError = type("FP_ReadOnlyError", (Exception,), {})
    flexicon_flex.FP_NullParameterError = type("FP_NullParameterError", (Exception,), {})

    base_ops = types.ModuleType("flexicon.code.BaseOperations")
    string_utils = types.ModuleType("flexicon.code.Shared.string_utils")
    string_utils.normalize_match_key = lambda s: s

    class _BaseOperations:
        def __init__(self, project):
            self.project = project

        def _EnsureWriteEnabled(self):
            if not getattr(self.project, "writeEnabled", False):
                raise flexicon_flex.FP_ReadOnlyError()

        def _ValidateParam(self, value, name):
            if value is None:
                raise flexicon_flex.FP_NullParameterError()

        def _TransactionCM(self, _label):
            cm = MagicMock()
            cm.__enter__ = Mock(return_value=None)
            cm.__exit__ = Mock(return_value=False)
            return cm

    def _operations_method(fn):
        return fn

    base_ops.BaseOperations = _BaseOperations
    base_ops.OperationsMethod = _operations_method
    base_ops.wrap_enumerable = lambda x: x

    sil_lcm = types.ModuleType("SIL.LCModel")
    sil_kernel = types.ModuleType("SIL.LCModel.Core.KernelInterfaces")
    sil_text = types.ModuleType("SIL.LCModel.Core.Text")
    for name in (
        "ICmLocation",
        "ICmLocationFactory",
        "ICmLocationRepository",
        "ICmPossibility",
        "ICmPossibilityFactory",
        "ICmPossibilityRepository",
    ):
        setattr(sil_lcm, name, type(name, (), {}))
    sil_kernel.ITsString = type("ITsString", (), {})
    sil_text.TsStringUtils = type("TsStringUtils", (), {})

    sys.modules["flexicon"] = flexicon
    sys.modules["flexicon.code"] = flexicon_code
    sys.modules["flexicon.code.FLExProject"] = flexicon_flex
    sys.modules["flexicon.code.BaseOperations"] = base_ops
    sys.modules["flexicon.code.Shared.string_utils"] = string_utils
    sys.modules["SIL"] = types.ModuleType("SIL")
    sys.modules["SIL.LCModel"] = sil_lcm
    sys.modules["SIL.LCModel.Core.KernelInterfaces"] = sil_kernel
    sys.modules["SIL.LCModel.Core.Text"] = sil_text
    sys.modules["System"] = types.ModuleType("System")
    from datetime import datetime

    sys.modules["System"].DateTime = type(
        "DateTime",
        (),
        {"Now": datetime.now()},
    )
    return flexicon_flex


class _MockOwningSequence:
    def __init__(self, items=None):
        self._items = list(items or [])
        self.remove_calls = []
        self.add_calls = []
        self.move_to_calls = []

    @property
    def Count(self):
        return len(self._items)

    def __contains__(self, item):
        return item in self._items

    def IndexOf(self, item):
        try:
            return self._items.index(item)
        except ValueError:
            return -1

    def Add(self, item):
        self.add_calls.append(item)
        if item not in self._items:
            self._items.append(item)

    def Remove(self, item):
        self.remove_calls.append(item)
        if item in self._items:
            self._items.remove(item)

    def MoveTo(self, i, j, seq, target):
        self.move_to_calls.append((i, j, seq, target))


class _FakeLocation:
    ClassName = "CmLocation"

    def __init__(self, guid=b"loc"):
        self.Guid = guid
        self.SubPossibilitiesOS = _MockOwningSequence()
        self.DateModified = None
        self.Hvo = id(self)


class _FakeLocationList:
    def __init__(self):
        self.PossibilitiesOS = _MockOwningSequence()


def _load_location_ops():
    _stub_flexicon_packages()
    path = _repo_root() / "flexicon" / "code" / "Notebook" / "LocationOperations.py"
    mod_name = "flexicon.code.Notebook.LocationOperations"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "flexicon.code.Notebook"
    sys.modules[mod_name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    mod.ICmLocation = lambda o: o
    return mod


class TestIssue472SetRegion:
    def test_set_region_reparents_with_add_only(self, monkeypatch):
        mod = _load_location_ops()
        project = Mock(writeEnabled=True)
        location_list = _FakeLocationList()
        project.lp = Mock(LocationsOA=location_list)
        ops = mod.LocationOperations(project)

        region_a = _FakeLocation(b"a")
        region_b = _FakeLocation(b"b")
        village = _FakeLocation(b"v")
        region_a.SubPossibilitiesOS.Add(village)

        monkeypatch.setattr(ops, "_LocationOperations__ResolveObject", lambda x: x)
        monkeypatch.setattr(ops, "GetRegion", lambda loc: region_a if loc is village else None)

        ops.SetRegion(village, region_b)

        assert region_b.SubPossibilitiesOS.add_calls == [village]
        assert region_a.SubPossibilitiesOS.remove_calls == []
        assert location_list.PossibilitiesOS.remove_calls == []


class TestIssue472SetRegionRatchet:
    def test_set_region_has_no_remove_on_location(self):
        path = _repo_root() / "flexicon" / "code" / "Notebook" / "LocationOperations.py"
        source = path.read_text(encoding="utf-8")
        module = ast.parse(source)
        for node in module.body:
            if not isinstance(node, ast.ClassDef) or node.name != "LocationOperations":
                continue
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "SetRegion":
                    body_src = ast.get_source_segment(source, item) or ""
                    assert ".Remove(location)" not in body_src, (
                        "SetRegion must not Remove(location) (#472)."
                    )
                    return
        raise AssertionError("SetRegion not found")


def _load_publication_ops():
    flexicon_flex = _stub_flexicon_packages()
    lists_pkg = types.ModuleType("flexicon.code.Lists")
    sys.modules["flexicon.code.Lists"] = lists_pkg

    poss_base_path = _repo_root() / "flexicon" / "code" / "Lists" / "possibility_item_base.py"
    poss_mod_name = "flexicon.code.Lists.possibility_item_base"
    spec = importlib.util.spec_from_file_location(poss_mod_name, poss_base_path)
    poss_mod = importlib.util.module_from_spec(spec)
    poss_mod.__package__ = "flexicon.code.Lists"
    sys.modules[poss_mod_name] = poss_mod
    assert spec.loader is not None
    spec.loader.exec_module(poss_mod)

    path = _repo_root() / "flexicon" / "code" / "Lists" / "PublicationOperations.py"
    mod_name = "flexicon.code.Lists.PublicationOperations"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "flexicon.code.Lists"
    sys.modules[mod_name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestIssue472SetIsDefault:
    def test_set_default_uses_move_to_not_remove(self, monkeypatch):
        mod = _load_publication_ops()
        project = Mock(writeEnabled=True)
        seq = _MockOwningSequence()
        pub_a = Mock(Hvo=1)
        pub_b = Mock(Hvo=2)
        seq._items = [pub_a, pub_b]
        pub_list = Mock(PossibilitiesOS=seq)
        project.lexDB = Mock(PublicationTypesOA=pub_list)

        ops = mod.PublicationOperations(project)
        monkeypatch.setattr(
            ops,
            "_PossibilityItemOperations__ResolveObject",
            lambda x: pub_b,
        )

        ops.SetIsDefault(pub_b, True)

        assert seq.remove_calls == []
        assert seq.move_to_calls == [(1, 1, seq, 0)]

    def test_clear_default_moves_to_end_with_move_to(self, monkeypatch):
        mod = _load_publication_ops()
        project = Mock(writeEnabled=True)
        seq = _MockOwningSequence()
        pub_a = Mock(Hvo=1)
        pub_b = Mock(Hvo=2)
        seq._items = [pub_a, pub_b]
        pub_list = Mock(PossibilitiesOS=seq)
        project.lexDB = Mock(PublicationTypesOA=pub_list)

        ops = mod.PublicationOperations(project)
        monkeypatch.setattr(
            ops,
            "_PossibilityItemOperations__ResolveObject",
            lambda x: pub_a,
        )

        ops.SetIsDefault(pub_a, False)

        assert seq.remove_calls == []
        assert seq.move_to_calls == [(0, 0, seq, 2)]


class TestIssue472SetIsDefaultRatchet:
    def test_set_is_default_has_no_remove(self):
        path = _repo_root() / "flexicon" / "code" / "Lists" / "PublicationOperations.py"
        source = path.read_text(encoding="utf-8")
        module = ast.parse(source)
        for node in module.body:
            if not isinstance(node, ast.ClassDef) or node.name != "PublicationOperations":
                continue
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "SetIsDefault":
                    body_src = ast.get_source_segment(source, item) or ""
                    assert ".Remove(publication)" not in body_src
                    assert ".Insert(0, publication)" not in body_src
                    return
        raise AssertionError("SetIsDefault not found")
