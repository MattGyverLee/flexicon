#
#   test_issue510_discourse_chart_row_resolver_offline.py
#
#   Offline ratchet for issue #510 chart/row resolver cast alignment.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DISCOURSE = REPO_ROOT / "flexicon" / "code" / "TextsWords" / "DiscourseOperations.py"
CHART_REF = REPO_ROOT / "flexicon" / "code" / "Discourse" / "ConstChartOperations.py"
ROW_REF = REPO_ROOT / "flexicon" / "code" / "Discourse" / "ConstChartRowOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue510_discourse_chart_row_resolver_live.py"
)


def _block(text: str, name: str) -> str:
    start = text.index(f"def {name}")
    next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue510_chart_reference_has_classname_pass_through():
    block = _block(CHART_REF.read_text(encoding="utf-8"), "__ResolveObject")
    assert 'ClassName", None) == "DsConstChart"' in block
    assert "return chart_or_hvo" in block


def test_issue510_get_chart_object_has_classname_pass_through():
    body = DISCOURSE.read_text(encoding="utf-8")
    block = _block(body, "__GetChartObject")
    assert "issue #510" in block
    assert "DsConstChart" in block and "DsChart" in block
    assert "__CastChartView" in body


def test_issue510_get_row_object_matches_row_resolver_pattern():
    row_block = _block(ROW_REF.read_text(encoding="utf-8"), "__ResolveObject")
    block = _block(DISCOURSE.read_text(encoding="utf-8"), "__GetRowObject")
    assert 'ClassName", None) == "ConstChartRow"' in row_block
    assert 'ClassName", None) == "ConstChartRow"' in block
    assert "return row_or_hvo" in block


def test_issue510_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #510"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Object(" in body
