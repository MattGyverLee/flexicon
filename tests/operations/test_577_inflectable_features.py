"""
Test Suite for InflectionFeatureOperations inflectable-feature wrappers

Coverage for issue #577:

- ``GetInflectableFeatures(pos_or_hvo)`` reads
  ``IPartOfSpeech.InflectableFeatsRC`` and casts each element to its
  concrete interface (``IFsClosedFeature`` / ``IFsComplexFeature``), so
  callers can read ``.Name``/``.Abbreviation`` without ``ClassName``
  probing -- the same ``IFsClosedFeature(raw)`` interface-call idiom
  that PhonFeatureOperations uses on read.
- ``GetFeatureType(feature_or_hvo)`` discriminates on
  ``IFsFeatDefn.ClassName``: ``"FsClosedFeature"`` -> ``"closed"``,
  ``"FsComplexFeature"`` -> ``"complex"``, raw ``ClassName`` fallback
  for future subtypes -- mirroring ``NaturalClassOperations.GetType``.

Uses mocks for the FLExProject/LCM layer -- no live FieldWorks project
required.

Author: Programmer Team - API coverage (#577)
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from flexicon.code.Grammar.InflectionFeatureOperations import (
    InflectionFeatureOperations,
)
from flexicon.code.FLExProject import FP_NullParameterError

_MODULE = "flexicon.code.Grammar.InflectionFeatureOperations"


class _FakeFeature:
    """Minimal stand-in for an IFsFeatDefn with a real ClassName."""

    def __init__(self, class_name, hvo=1):
        self.ClassName = class_name
        self.Hvo = hvo


class _FakePOS:
    """Minimal stand-in for an IPartOfSpeech with an InflectableFeatsRC."""

    def __init__(self, features, hvo=3000):
        self.ClassName = "PartOfSpeech"
        self.Hvo = hvo
        self.InflectableFeatsRC = features


def _make_project(pos):
    """Build a minimal mock FLExProject that resolves the POS by HVO."""
    project = Mock()
    project.Object = Mock(side_effect=lambda hvo: pos if hvo == pos.Hvo else Mock())
    return project


@pytest.fixture
def ops_and_pos():
    closed = _FakeFeature("FsClosedFeature", hvo=101)
    complex_feat = _FakeFeature("FsComplexFeature", hvo=102)
    future = _FakeFeature("FsOpenFeature", hvo=103)
    pos = _FakePOS([closed, complex_feat, future])
    project = _make_project(pos)
    ops = InflectionFeatureOperations(project)
    return ops, project, pos, closed, complex_feat, future


@pytest.fixture(autouse=True)
def _identity_cast_to_concrete():
    """Keep object resolution hermetic: real pythonnet casts cannot run
    on fakes, and the discrimination logic under test sits after them."""
    with patch(_MODULE + ".cast_to_concrete", side_effect=lambda o: o):
        yield


class TestGetFeatureType:
    """Issue #577: GetFeatureType discriminates on ClassName."""

    def test_closed_feature_returns_closed(self, ops_and_pos):
        ops, _, _, closed, _, _ = ops_and_pos
        assert ops.GetFeatureType(closed) == "closed"

    def test_complex_feature_returns_complex(self, ops_and_pos):
        ops, _, _, _, complex_feat, _ = ops_and_pos
        assert ops.GetFeatureType(complex_feat) == "complex"

    def test_future_subtype_returns_raw_classname(self, ops_and_pos):
        # Defensive fallback, mirroring NaturalClassOperations.GetType.
        ops, _, _, _, _, future = ops_and_pos
        assert ops.GetFeatureType(future) == "FsOpenFeature"

    def test_hvo_input_resolves_through_project_object(self, ops_and_pos):
        ops, project, _, closed, _, _ = ops_and_pos
        assert ops.GetFeatureType(closed.Hvo) == "closed"
        project.Object.assert_called_with(closed.Hvo)

    def test_none_raises_null_parameter_error(self, ops_and_pos):
        ops, _, _, _, _, _ = ops_and_pos
        with pytest.raises(FP_NullParameterError):
            ops.GetFeatureType(None)


class TestGetInflectableFeatures:
    """Issue #577: GetInflectableFeatures reads InflectableFeatsRC cast."""

    def _casters(self):
        """Tagging factories that record which concrete cast each raw took."""
        return {
            "IFsClosedFeature": Mock(side_effect=lambda raw: ("closed", raw)),
            "IFsComplexFeature": Mock(side_effect=lambda raw: ("complex", raw)),
            "IFsFeatDefn": Mock(side_effect=lambda raw: ("featdefn", raw)),
        }

    def test_casts_each_element_to_concrete_interface(self, ops_and_pos):
        ops, _, pos, closed, complex_feat, future = ops_and_pos
        casters = self._casters()
        with patch(_MODULE + ".IFsClosedFeature", casters["IFsClosedFeature"]), \
             patch(_MODULE + ".IFsComplexFeature", casters["IFsComplexFeature"]), \
             patch(_MODULE + ".IFsFeatDefn", casters["IFsFeatDefn"]):
            feats = ops.GetInflectableFeatures(pos)

        assert feats == [
            ("closed", closed),
            ("complex", complex_feat),
            ("featdefn", future),
        ]
        casters["IFsClosedFeature"].assert_called_once_with(closed)
        casters["IFsComplexFeature"].assert_called_once_with(complex_feat)
        casters["IFsFeatDefn"].assert_called_once_with(future)

    def test_hvo_input_resolves_through_project_object(self, ops_and_pos):
        ops, project, pos, closed, _, _ = ops_and_pos
        casters = self._casters()
        with patch(_MODULE + ".IFsClosedFeature", casters["IFsClosedFeature"]), \
             patch(_MODULE + ".IFsComplexFeature", casters["IFsComplexFeature"]), \
             patch(_MODULE + ".IFsFeatDefn", casters["IFsFeatDefn"]):
            feats = ops.GetInflectableFeatures(pos.Hvo)

        project.Object.assert_called_with(pos.Hvo)
        assert [tag for tag, _ in feats] == ["closed", "complex", "featdefn"]

    def test_empty_inflectable_feats_returns_empty_list(self, ops_and_pos):
        ops, _, _, _, _, _ = ops_and_pos
        empty_pos = _FakePOS([])
        assert ops.GetInflectableFeatures(empty_pos) == []

    def test_none_raises_null_parameter_error(self, ops_and_pos):
        ops, _, _, _, _, _ = ops_and_pos
        with pytest.raises(FP_NullParameterError):
            ops.GetInflectableFeatures(None)
