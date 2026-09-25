#
#   test_issue494_contract_resolvers_offline.py
#
#   Offline ratchet for issue #494 contract-only resolver docstrings.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_issue494_featstruc_operand_docstring_promises_no_cast():
    text = _read("flexicon/code/BaseOperations.py")
    start = text.index("def __ResolveFeatStrucOperand(")
    block = text[start : text.index("\n    @staticmethod", start)]
    assert "intentionally does **not** cast" in block
    assert "issue #494" in block


def test_issue494_phonological_rule_resolver_docstrings():
    text = _read("flexicon/code/Grammar/PhonologicalRuleOperations.py")
    feat_start = text.index("def __ResolveFeature(")
    feat_block = text[feat_start : text.index("def __ResolveLcmObject(", feat_start)]
    assert "without ``cast_to_concrete``" in feat_block
    assert "issue #494" in feat_block

    lcm_start = text.index("def __ResolveLcmObject(")
    lcm_block = text[lcm_start : text.index("def Duplicate(", lcm_start)]
    assert "without casting so object identity" in lcm_block
    assert "#494" in lcm_block


def test_issue494_scrnote_paragraph_docstring():
    text = _read("flexicon/code/Scripture/ScrNoteOperations.py")
    start = text.index("def __ResolveParagraph(")
    block = text[start : text.index("def __WSHandle(", start)]
    assert "does not call\n            ``cast_to_concrete``" in block or (
        "does not call" in block and "cast_to_concrete" in block
    )
    assert "issue #494" in block


def test_issue494_segment_analysis_docstring():
    text = _read("flexicon/code/TextsWords/SegmentOperations.py")
    start = text.index("def __GetAnalysisObject(")
    block = text[start : text.index("def GetAll(", start)]
    assert "without ``cast_to_concrete``" in block
    assert "issue #212" in block
    assert "issue #494" in block
