#
#   test_issue684_example_movemedia_hvo_offline.py
#
#   Issue #684 asked for HVO-based membership in Example MoveMediaFile.
#   Issue #831 withdrew the Example media methods entirely (no MediaFilesOS
#   on ILexExampleSentence), so the HVO-membership code is gone. This ratchet
#   now locks that MoveMediaFile contains no MediaFilesOS code path.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
EXAMPLE_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "ExampleOperations.py"
LIVE_GATE = REPO_ROOT / "tests" / "operations" / "test_issue684_example_movemedia_hvo_live.py"


def _move_media_block(text: str) -> str:
    start = text.index("def MoveMediaFile(self, media, from_example_or_hvo, to_example_or_hvo):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def _code_lines(block: str) -> str:
    """Strip the docstring so prose mentioning MediaFilesOS is ignored."""
    first = block.index('"""')
    last = block.index('"""', first + 3) + 3
    return block[:first] + block[last:]


def test_issue684_move_media_has_no_mediafilesos_code():
    code = _code_lines(_move_media_block(EXAMPLE_OPS.read_text(encoding="utf-8")))
    assert "MediaFilesOS" not in code
    assert "target_hvo" not in code
    assert ".Add(" not in code
    assert "_TransactionCM" not in code


def test_issue684_move_media_warns_then_raises():
    code = _code_lines(_move_media_block(EXAMPLE_OPS.read_text(encoding="utf-8")))
    assert "DeprecationWarning" in code
    assert "raise FP_ParameterError" in code


def test_issue684_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #684"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "MoveMediaFile" in body
