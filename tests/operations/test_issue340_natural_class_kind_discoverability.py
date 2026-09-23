#
#   test_issue340_natural_class_kind_discoverability.py
#
#   Offline tests for issue #340: boolean kind helpers and AddPhoneme
#   pre-check discoverability (IsFeatureBased / IsSegmentBased).
#
#   Platform: Python.NET (FieldWorks optional -- uses simple fakes)
#
#   Copyright 2026
#

from pathlib import Path

import pytest

_NATURAL_CLASS_OPS = (
    Path(__file__).resolve().parents[2]
    / "flexicon"
    / "code"
    / "Grammar"
    / "NaturalClassOperations.py"
)


class TestIssue340Static:
    """Source locks that run without SIL.LCModel (cloud/CI safe)."""

    def test_is_feature_based_and_is_segment_based_methods_exist(self):
        src = _NATURAL_CLASS_OPS.read_text(encoding="utf-8")
        assert "def IsFeatureBased(self, nc_or_hvo):" in src
        assert "def IsSegmentBased(self, nc_or_hvo):" in src
        assert 'return self.GetType(nc_or_hvo) == "features"' in src
        assert 'return self.GetType(nc_or_hvo) == "segments"' in src

    def test_add_phoneme_guard_names_discoverability_helpers(self):
        src = _NATURAL_CLASS_OPS.read_text(encoding="utf-8")
        assert "if not self.IsSegmentBased(nc):" in src
        assert "IsFeatureBased()" in src
        assert "GetType()" in src


class _FakeProject:
    writeEnabled = True

    def Object(self, hvo):
        return hvo


class _FakeSegmentsNC:
    ClassName = "PhNCSegments"

    def __init__(self):
        self.SegmentsRC = []


class _FakeFeaturesNC:
    ClassName = "PhNCFeatures"

    def __init__(self):
        self.FeaturesOA = None


@pytest.fixture
def _require_lcmodel():
    pytest.importorskip("SIL.LCModel")


@pytest.mark.usefixtures("_require_lcmodel")
def test_is_segment_based_and_is_feature_based():
    from flexicon.code.Grammar.NaturalClassOperations import (
        NaturalClassOperations,
    )

    ops = NaturalClassOperations(_FakeProject())
    seg = _FakeSegmentsNC()
    feat = _FakeFeaturesNC()

    assert ops.IsSegmentBased(seg) is True
    assert ops.IsFeatureBased(seg) is False
    assert ops.IsSegmentBased(feat) is False
    assert ops.IsFeatureBased(feat) is True


@pytest.mark.usefixtures("_require_lcmodel")
def test_add_phoneme_error_names_discoverability_helpers():
    from flexicon.code.FLExProject import FP_ParameterError
    from flexicon.code.Grammar.NaturalClassOperations import (
        NaturalClassOperations,
    )

    ops = NaturalClassOperations(_FakeProject())
    feat = _FakeFeaturesNC()
    phoneme = object()

    with pytest.raises(FP_ParameterError) as exc:
        ops.AddPhoneme(feat, phoneme)

    msg = str(exc.value)
    assert "IsFeatureBased" in msg
    assert "GetType" in msg


@pytest.mark.usefixtures("_require_lcmodel")
def test_is_feature_based_allows_branch_before_add_phoneme():
    """Callers can skip feature-based classes without hitting AddPhoneme."""
    from flexicon.code.Grammar.NaturalClassOperations import (
        NaturalClassOperations,
    )

    ops = NaturalClassOperations(_FakeProject())
    seg = _FakeSegmentsNC()
    feat = _FakeFeaturesNC()
    phoneme = object()

    for nc in (seg, feat):
        if ops.IsFeatureBased(nc):
            continue
        ops.AddPhoneme(nc, phoneme)

    assert phoneme in seg.SegmentsRC
    assert feat.FeaturesOA is None
