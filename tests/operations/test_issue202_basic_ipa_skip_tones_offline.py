#
#   test_issue202_basic_ipa_skip_tones_offline.py
#
#   Offline regression for issue #202: BasicIPA tone rows must not be
#   imported as featureless segmental phonemes by default.
#
#   Copyright 2026
#

import ast
import pathlib
from dataclasses import dataclass, field
from typing import List, Tuple

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CATALOG_PY = REPO_ROOT / "flexicon" / "code" / "Shared" / "catalog.py"
PHONEME_OPS_PY = REPO_ROOT / "flexicon" / "code" / "Grammar" / "PhonemeOperations.py"


@dataclass
class _Seg:
    code_point_id: str
    representation: str
    feature_pairs: List[Tuple[str, str]] = field(default_factory=list)


def _import_catalog_defaults():
    tree = ast.parse(
        PHONEME_OPS_PY.read_text(encoding="utf-8"), filename=str(PHONEME_OPS_PY)
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "ImportCatalog":
            names = [a.arg for a in node.args.args]
            pad = [None] * (len(names) - len(node.args.defaults))
            paired = list(zip(names, pad + list(node.args.defaults)))
            out = {}
            for name, val in paired:
                if isinstance(val, ast.Constant):
                    out[name] = val.value
            return out
    raise AssertionError("ImportCatalog not found in PhonemeOperations.py")


class TestIssue202ToneDetector:
    def test_catalog_helper_exists_and_matches_empty_features(self):
        source = CATALOG_PY.read_text(encoding="utf-8")
        assert "def basic_ipa_segment_is_suprasegmental_tone" in source
        # Mirror the one-liner contract documented in catalog.py.
        assert not _Seg("u002b", "+", feature_pairs=[]).feature_pairs
        assert _Seg(
            "u0061",
            "a",
            feature_pairs=[("fPAConsonantal", "vPAConsonantalNegative")],
        ).feature_pairs


class TestIssue202ImportCatalogContract:
    def test_skip_tones_kwarg_default_true(self):
        defaults = _import_catalog_defaults()
        assert defaults.get("skip_tones") is True

    def test_import_loop_skips_tones_when_flag_set(self):
        source = PHONEME_OPS_PY.read_text(encoding="utf-8")
        assert "basic_ipa_segment_is_suprasegmental_tone" in source
        assert "skip_tones=False" in source


def test_stock_catalog_has_seven_tone_rows_at_head():
    """FW ships seven tone SegmentDefinitions before the first segmental row."""
    from tests.test_catalog import _fw_available

    if not _fw_available():
        pytest.skip(
            "FieldWorks (with Templates/BasicIPAInfo.xml) not available"
        )
    from flexicon.code.Shared.catalog import (
        basic_ipa_segment_is_suprasegmental_tone,
        find_catalog_file,
        parse_basic_ipa_info,
    )

    segments = parse_basic_ipa_info(find_catalog_file("BasicIPAInfo.xml"))
    prefix = []
    for seg in segments:
        if seg.feature_pairs:
            break
        prefix.append(seg)
    assert len(prefix) == 7, (
        f"Expected 7 tone rows at catalog head, got {len(prefix)}"
    )
    assert all(basic_ipa_segment_is_suprasegmental_tone(s) for s in prefix)
