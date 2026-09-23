#
#   test_issue301_unordered_getsequence.py
#
#   Regression coverage for issue #301: WfiAnalysisOperations and
#   PhonemeOperations must not read nonexistent ...OS properties on
#   unordered ...OC collections; reorder hooks raise NotImplementedError.
#

import ast
from pathlib import Path

import pytest

try:
    import clr  # noqa: F401

    _HAS_CLR = True
except Exception:
    _HAS_CLR = False

REPO = Path(__file__).resolve().parents[2]
WFI_PATH = REPO / "flexicon/code/TextsWords/WfiAnalysisOperations.py"
PHONEME_PATH = REPO / "flexicon/code/Grammar/PhonemeOperations.py"


def _get_sequence_body(source_path: Path) -> ast.FunctionDef:
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_GetSequence":
            return node
    raise AssertionError(f"_GetSequence not found in {source_path}")


def _body_source(source_path: Path, func: ast.FunctionDef) -> str:
    lines = source_path.read_text(encoding="utf-8").splitlines()
    start = func.lineno - 1
    end = func.end_lineno
    return "\n".join(lines[start:end])


class TestIssue301SourceRatchet:
    def test_wfi_analysis_no_analyses_os_return(self):
        func = _get_sequence_body(WFI_PATH)
        body = _body_source(WFI_PATH, func)
        assert "AnalysesOS" not in body or "no ``AnalysesOS``" in body
        assert "raise NotImplementedError" in body
        assert "AnalysesOC" in body
        assert "unordered" in body.lower()

    def test_phoneme_no_phonemes_os_return(self):
        func = _get_sequence_body(PHONEME_PATH)
        body = _body_source(PHONEME_PATH, func)
        assert "return parent.PhonemesOS" not in body
        assert "raise NotImplementedError" in body
        assert "PhonemesOC" in body
        assert "unordered" in body.lower()


class _MockSelf:
    """Minimal Operations stand-in for direct _GetSequence calls."""


@pytest.mark.skipif(not _HAS_CLR, reason="pythonnet runtime unavailable")
class TestIssue301RuntimeGetSequence:
    def test_wfi_analysis_get_sequence_raises(self):
        from flexicon.code.TextsWords.WfiAnalysisOperations import (
            WfiAnalysisOperations,
        )

        with pytest.raises(NotImplementedError) as exc_info:
            WfiAnalysisOperations._GetSequence(_MockSelf(), object())
        msg = str(exc_info.value).lower()
        assert "unordered" in msg
        assert "analysesoc" in msg.replace(" ", "")

    def test_phoneme_get_sequence_raises(self):
        from flexicon.code.Grammar.PhonemeOperations import PhonemeOperations

        with pytest.raises(NotImplementedError) as exc_info:
            PhonemeOperations._GetSequence(_MockSelf(), object())
        msg = str(exc_info.value).lower()
        assert "unordered" in msg
        assert "phonemesoc" in msg.replace(" ", "")
