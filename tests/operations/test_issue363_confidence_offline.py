#
#   test_issue363_confidence_offline.py
#
#   Offline coverage for issue #363 without importing flexicon (no LCM on Linux CI).
#
#   Copyright 2026
#

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CONF_OPS = REPO_ROOT / "flexicon" / "code" / "Lists" / "ConfidenceOperations.py"


def _method_body(source: str, method_name: str) -> str:
    match = re.search(
        rf"def {method_name}\(.*?(?=\n    def |\n    # ---|\nclass |\Z)",
        source,
        re.DOTALL,
    )
    assert match is not None, f"{method_name} not found"
    return match.group(0)


def test_get_analyses_with_confidence_scans_notebook_records():
    source = CONF_OPS.read_text(encoding="utf-8")
    body = _method_body(source, "GetAnalysesWithConfidence")
    assert "IWfiAnalysisRepository" not in body
    assert "ConfidenceRA" in body
    assert "hasattr" not in body
    assert "DataNotebook.GetAll()" in body


def test_get_glosses_with_confidence_raises_parameter_error():
    source = CONF_OPS.read_text(encoding="utf-8")
    body = _method_body(source, "GetGlossesWithConfidence")
    assert "IWfiGlossRepository" not in body
    assert "hasattr" not in body
    assert "gloss.ConfidenceRA" not in body
    assert "raise FP_ParameterError" in body
    assert "IWfiGloss" in body
