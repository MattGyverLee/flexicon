#
#   test_issue281_lcm_casting_logger.py
#
#   Offline regression for issue #281: lcm_casting.py must expose a module
#   logger; import logging must not be stranded inside the docstring.
#
#   Copyright 2026
#

import ast
from pathlib import Path


def _lcm_casting_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "flexicon"
        / "code"
        / "lcm_casting.py"
    )


def test_issue281_import_logging_not_in_module_docstring():
    source = _lcm_casting_path().read_text(encoding="utf-8")
    module = ast.parse(source)
    doc = ast.get_docstring(module)
    assert doc is not None
    assert "import logging" not in doc, (
        "import logging must not live inside the module docstring (issue #281)"
    )


def test_issue281_module_logger_defined():
    source = _lcm_casting_path().read_text(encoding="utf-8")
    assert "logger = logging.getLogger(__name__)" in source
    tree = ast.parse(source)
    names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    assert "logger" in names


def test_issue281_cast_to_concrete_logs_unregistered_classname(monkeypatch):
    """Unregistered ClassName no-op emits debug (issue #281)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "lcm_casting_issue281",
        _lcm_casting_path(),
    )
    lcm_casting = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(lcm_casting)

    messages = []

    def _capture(msg, *args):
        messages.append(msg % args if args else msg)

    monkeypatch.setattr(lcm_casting.logger, "debug", _capture)
    lcm_casting._interface_cache.clear()
    lcm_casting._interfaces_loaded = True

    class _Obj:
        ClassName = "TotallyUnregisteredClassNameFor281"

    result = lcm_casting.cast_to_concrete(_Obj())
    assert result.ClassName == "TotallyUnregisteredClassNameFor281"
    assert any("interface cache" in m for m in messages)
