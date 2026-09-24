#
#   test_issue448_move_item_offline.py
#
#   Offline coverage for issue #448: PossibilityListOperations.MoveItem
#   and GetParentItem must treat CmPossibility subclasses as parents and
#   must re-parent via Add only (never Remove-then-Add).
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


def _ops_module_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "flexicon"
        / "code"
        / "Lists"
        / "PossibilityListOperations.py"
    )


def _load_possibility_list_ops():
    """Load PossibilityListOperations without flexicon package init or CLR."""
    flexicon = types.ModuleType("flexicon")
    flexicon_code = types.ModuleType("flexicon.code")
    flexicon_lists = types.ModuleType("flexicon.code.Lists")
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

        def _GetTypedElements(self, gen):
            return list(gen)

        def _TransactionCM(self, _label):
            cm = MagicMock()
            cm.__enter__ = Mock(return_value=None)
            cm.__exit__ = Mock(return_value=False)
            return cm

        def _RejectLegacyKwargs(self, kwargs, mapping):
            pass

    def _operations_method(fn):
        return fn

    base_ops.BaseOperations = _BaseOperations
    base_ops.OperationsMethod = _operations_method

    sil_lcm = types.ModuleType("SIL.LCModel")
    sil_kernel = types.ModuleType("SIL.LCModel.Core.KernelInterfaces")
    sil_text = types.ModuleType("SIL.LCModel.Core.Text")

    for name in (
        "ICmPossibility",
        "ICmPossibilityFactory",
        "ICmPossibilityList",
        "ICmPossibilityListFactory",
        "ICmPossibilityRepository",
    ):
        setattr(sil_lcm, name, type(name, (), {}))

    sil_kernel.ITsString = type("ITsString", (), {})
    sil_text.TsStringUtils = type("TsStringUtils", (), {})

    sys.modules["flexicon"] = flexicon
    sys.modules["flexicon.code"] = flexicon_code
    sys.modules["flexicon.code.Lists"] = flexicon_lists
    sys.modules["flexicon.code.FLExProject"] = flexicon_flex
    sys.modules["flexicon.code.BaseOperations"] = base_ops
    sys.modules["flexicon.code.Shared.string_utils"] = string_utils
    sys.modules["SIL"] = types.ModuleType("SIL")
    sys.modules["SIL.LCModel"] = sil_lcm
    sys.modules["SIL.LCModel.Core.KernelInterfaces"] = sil_kernel
    sys.modules["SIL.LCModel.Core.Text"] = sil_text
    sys.modules["System"] = types.ModuleType("System")

    mod_name = "flexicon.code.Lists.PossibilityListOperations"
    spec = importlib.util.spec_from_file_location(mod_name, _ops_module_path())
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "flexicon.code.Lists"
    sys.modules[mod_name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    mod.ICmPossibility = lambda o: o
    mod.ICmPossibilityList = lambda o: o
    return mod


class _MockOwningSequence:
    """Minimal LcmOwningSequence stand-in: Remove deletes; Add re-parents."""

    def __init__(self):
        self._items = []
        self.remove_calls = []
        self.add_calls = []

    def Add(self, item):
        self.add_calls.append(item)
        if item not in self._items:
            self._items.append(item)

    def Remove(self, item):
        self.remove_calls.append(item)
        if item in self._items:
            self._items.remove(item)


class _FakePossibilityList:
    ClassName = "CmPossibilityList"

    def __init__(self, guid=b"list-guid"):
        self.Guid = guid
        self.PossibilitiesOS = _MockOwningSequence()


class _FakePossibility:
    def __init__(self, class_name, guid, owner=None):
        self.ClassName = class_name
        self.Guid = guid
        self.Owner = owner
        self.SubPossibilitiesOS = _MockOwningSequence()
        self.Hvo = id(self)


class TestIssue448GetParentItem:
    def test_part_of_speech_owner_is_parent(self):
        mod = _load_possibility_list_ops()
        project = Mock(writeEnabled=True)
        ops = mod.PossibilityListOperations(project)
        pos_list = _FakePossibilityList()
        parent = _FakePossibility("PartOfSpeech", b"parent-guid", owner=pos_list)
        child = _FakePossibility("PartOfSpeech", b"child-guid", owner=parent)

        assert ops.GetParentItem(child) is parent

    def test_top_level_owner_returns_none(self):
        mod = _load_possibility_list_ops()
        project = Mock(writeEnabled=True)
        ops = mod.PossibilityListOperations(project)
        pos_list = _FakePossibilityList()
        top = _FakePossibility("PartOfSpeech", b"top-guid", owner=pos_list)

        assert ops.GetParentItem(top) is None


class TestIssue448MoveItem:
    def test_move_to_top_level_add_only_no_remove(self, monkeypatch):
        mod = _load_possibility_list_ops()
        project = Mock(writeEnabled=True)
        ops = mod.PossibilityListOperations(project)
        pos_list = _FakePossibilityList()
        parent = _FakePossibility("PartOfSpeech", b"parent-guid", owner=pos_list)
        child = _FakePossibility("PartOfSpeech", b"child-guid", owner=parent)

        monkeypatch.setattr(
            ops,
            "_PossibilityListOperations__ResolveItem",
            lambda _x: child,
        )
        monkeypatch.setattr(
            ops,
            "_PossibilityListOperations__GetListOwner",
            lambda _item: pos_list,
        )
        monkeypatch.setattr(
            ops,
            "_PossibilityListOperations__IsDescendant",
            lambda _a, _b: False,
        )

        ops.MoveItem(child, None)

        assert pos_list.PossibilitiesOS.add_calls == [child]
        assert parent.SubPossibilitiesOS.remove_calls == [], (
            "MoveItem must not Remove before Add -- LCM deletes on Remove (#448)."
        )

    def test_move_under_new_parent_add_only(self, monkeypatch):
        mod = _load_possibility_list_ops()
        project = Mock(writeEnabled=True)
        ops = mod.PossibilityListOperations(project)
        pos_list = _FakePossibilityList()
        parent_a = _FakePossibility("PartOfSpeech", b"a", owner=pos_list)
        parent_b = _FakePossibility("PartOfSpeech", b"b", owner=pos_list)
        child = _FakePossibility("PartOfSpeech", b"c", owner=parent_a)

        monkeypatch.setattr(
            ops,
            "_PossibilityListOperations__ResolveItem",
            lambda x: parent_b if x is parent_b else child,
        )
        monkeypatch.setattr(
            ops,
            "_PossibilityListOperations__GetListOwner",
            lambda _item: pos_list,
        )
        monkeypatch.setattr(
            ops,
            "_PossibilityListOperations__IsDescendant",
            lambda _a, _b: False,
        )

        ops.MoveItem(child, parent_b)

        assert parent_b.SubPossibilitiesOS.add_calls == [child]
        assert parent_a.SubPossibilitiesOS.remove_calls == []


class TestIssue448MoveItemRatchet:
    def test_move_item_body_has_no_remove_on_item(self):
        source = _ops_module_path().read_text(encoding="utf-8")
        module = ast.parse(source)
        for node in module.body:
            if not isinstance(node, ast.ClassDef):
                continue
            if node.name != "PossibilityListOperations":
                continue
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "MoveItem":
                    body_src = ast.get_source_segment(source, item) or ""
                    assert ".Remove(item)" not in body_src, (
                        "MoveItem must not call Remove(item) (#448)."
                    )
                    return
        raise AssertionError("MoveItem not found")

    def test_get_parent_item_uses_owner_helper(self):
        source = _ops_module_path().read_text(encoding="utf-8")
        assert "__OwnerIsPossibilityItem" in source
        module = ast.parse(source)
        for node in module.body:
            if not isinstance(node, ast.ClassDef):
                continue
            if node.name != "PossibilityListOperations":
                continue
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "GetParentItem":
                    body_src = ast.get_source_segment(source, item) or ""
                    assert "__OwnerIsPossibilityItem" in body_src
                    assert 'ClassName == "CmPossibility"' not in body_src
                    return
        raise AssertionError("GetParentItem not found")
