#
#   test_issue473_scripture_discourse_move_offline.py
#
#   Offline coverage for issue #473: cross-owner MoveTo must re-parent via
#   Insert only (never Remove-then-Insert); same-owner via MoveTo.
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


_MOVE_SITES = (
    (
        _repo_root() / "flexicon" / "code" / "Scripture" / "ScrSectionOperations.py",
        "ScrSectionOperations",
        "MoveTo",
        "section",
    ),
    (
        _repo_root() / "flexicon" / "code" / "Discourse" / "ConstChartRowOperations.py",
        "ConstChartRowOperations",
        "MoveTo",
        "row",
    ),
)


def _stub_flexicon_packages():
    flexicon = types.ModuleType("flexicon")
    flexicon_code = types.ModuleType("flexicon.code")
    flexicon_flex = types.ModuleType("flexicon.code.FLExProject")
    flexicon_flex.FP_ParameterError = type("FP_ParameterError", (Exception,), {})
    flexicon_flex.FP_ReadOnlyError = type("FP_ReadOnlyError", (Exception,), {})
    flexicon_flex.FP_NullParameterError = type("FP_NullParameterError", (Exception,), {})

    base_ops = types.ModuleType("flexicon.code.BaseOperations")

    class _BaseOperations:
        def __init__(self, project):
            self.project = project

        def _EnsureWriteEnabled(self):
            if not getattr(self.project, "writeEnabled", False):
                raise flexicon_flex.FP_ReadOnlyError()

        def _ValidateParam(self, value, name):
            if value is None:
                raise flexicon_flex.FP_NullParameterError()

        def _GetTypedOwner(self, obj):
            return obj.Owner

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
        "IScrBook",
        "IScrSection",
        "IScrSectionFactory",
        "IScrTxtPara",
        "IStText",
        "IStTextFactory",
        "IConstChartRow",
        "IConstChartRowFactory",
        "IDsConstChart",
        "IConstChartWordGroup",
    ):
        setattr(sil_lcm, name, type(name, (), {}))
    sil_kernel.ITsString = type("ITsString", (), {})
    sil_text.TsStringUtils = type("TsStringUtils", (), {})

    sys.modules["flexicon"] = flexicon
    sys.modules["flexicon.code"] = flexicon_code
    sys.modules["flexicon.code.FLExProject"] = flexicon_flex
    sys.modules["flexicon.code.BaseOperations"] = base_ops
    sys.modules["SIL"] = types.ModuleType("SIL")
    sys.modules["SIL.LCModel"] = sil_lcm
    sys.modules["SIL.LCModel.Core.KernelInterfaces"] = sil_kernel
    sys.modules["SIL.LCModel.Core.Text"] = sil_text
    sys.modules["System"] = types.ModuleType("System")


def _method_source(path: Path, class_name: str, method_name: str) -> str:
    source = path.read_text(encoding="utf-8")
    module = ast.parse(source)
    for node in module.body:
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == method_name:
                return ast.get_source_segment(source, item) or ""
    raise AssertionError(f"{class_name}.{method_name} not found in {path}")


class _MockOwningSequence:
    def __init__(self):
        self._items = []
        self.remove_calls = []
        self.insert_calls = []
        self.move_to_calls = []

    def IndexOf(self, item):
        try:
            return self._items.index(item)
        except ValueError:
            return -1

    @property
    def Count(self):
        return len(self._items)

    def Insert(self, index, item):
        self.insert_calls.append((index, item))
        if item not in self._items:
            self._items.insert(index, item)

    def Remove(self, item):
        self.remove_calls.append(item)
        if item in self._items:
            self._items.remove(item)

    def MoveTo(self, i, j, seq, k):
        self.move_to_calls.append((i, j, seq, k))


def _load_scr_section_ops():
    _stub_flexicon_packages()
    path = _repo_root() / "flexicon" / "code" / "Scripture" / "ScrSectionOperations.py"
    mod_name = "flexicon.code.Scripture.ScrSectionOperations"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "flexicon.code.Scripture"
    sys.modules[mod_name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    mod.IScrSection = lambda o: o
    mod.IScrBook = lambda o: o
    return mod


def _load_const_chart_row_ops():
    _stub_flexicon_packages()
    path = _repo_root() / "flexicon" / "code" / "Discourse" / "ConstChartRowOperations.py"
    mod_name = "flexicon.code.Discourse.ConstChartRowOperations"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "flexicon.code.Discourse"
    sys.modules[mod_name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    mod.IConstChartRow = lambda o: o
    mod.IDsConstChart = lambda o: o
    return mod


class TestIssue473MoveRatchet:
    @pytest.mark.parametrize(
        "path,class_name,method_name,item_name",
        _MOVE_SITES,
        ids=["scr-section", "const-chart-row"],
    )
    def test_move_to_has_no_remove_on_item(self, path, class_name, method_name, item_name):
        body_src = _method_source(path, class_name, method_name)
        assert f".Remove({item_name})" not in body_src, (
            f"{class_name}.{method_name} must not call Remove({item_name}) (#473)."
        )


class TestIssue473ScrSectionMoveToCrossBook:
    def test_cross_book_insert_only_no_remove(self, monkeypatch):
        mod = _load_scr_section_ops()
        section = Mock()
        book_a = Mock()
        book_b = Mock()
        section.Owner = book_a
        book_a.SectionsOS = _MockOwningSequence()
        book_b.SectionsOS = _MockOwningSequence()

        project = Mock(writeEnabled=True)
        ops = mod.ScrSectionOperations(project)

        monkeypatch.setattr(ops, "_ScrSectionOperations__ResolveObject", lambda _x: section)
        monkeypatch.setattr(ops, "_ScrSectionOperations__ResolveBook", lambda _x: book_b)

        ops.MoveTo(section, book_b, 0)

        assert book_b.SectionsOS.insert_calls == [(0, section)]
        assert book_a.SectionsOS.remove_calls == []


class TestIssue473ConstChartRowMoveToCrossChart:
    def test_cross_chart_insert_only_no_remove(self, monkeypatch):
        mod = _load_const_chart_row_ops()
        row = Mock()
        source_chart = Mock()
        target_chart = Mock()
        source_chart.RowsOS = _MockOwningSequence()
        target_chart.RowsOS = _MockOwningSequence()

        project = Mock(writeEnabled=True)
        ops = mod.ConstChartRowOperations(project)

        monkeypatch.setattr(ops, "_ConstChartRowOperations__ResolveObject", lambda _x: row)
        monkeypatch.setattr(ops, "_ConstChartRowOperations__ResolveChart", lambda _x: target_chart)

        ops.MoveTo(row, target_chart, 0)

        assert target_chart.RowsOS.insert_calls == [(0, row)]
        assert source_chart.RowsOS.remove_calls == []
