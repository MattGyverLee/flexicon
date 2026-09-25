#
#   test_issue476_sysmodules_pollution_offline.py
#
#   Offline ratchet for GitHub issue #476:
#   clause-marker offline loader must register stand-ins via monkeypatch.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import re
from pathlib import Path

import pytest


def _loader_helper_source() -> str:
    path = Path(__file__).resolve().parent / "test_issue357_clause_marker_getwordgroup_offline.py"
    text = path.read_text(encoding="utf-8")
    start = text.index("def _load_const_chart_clause_marker_ops")
    end = text.index("\n\nclass _FakeCellsOS", start)
    return text[start:end]


class TestIssue476SysModulesPollutionRatchet:
    def test_loader_uses_monkeypatch_setitem_for_sys_modules(self):
        helper = _loader_helper_source()
        assert "monkeypatch.setitem(sys.modules" in helper
        assert re.search(r'sys\.modules\[[\'"]flexicon[\'"]\]\s*=', helper) is None

    def test_loader_does_not_assign_sys_modules_outside_monkeypatch(self):
        helper = _loader_helper_source()
        for line in helper.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "sys.modules[" in stripped and "monkeypatch.setitem" not in stripped:
                pytest.fail(f"plain sys.modules assignment: {stripped}")
