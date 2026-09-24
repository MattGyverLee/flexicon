#
#   test_issue265_makefeatstruc_names_offline.py
#
#   Offline coverage for MakeFeatStruc plain name operands (issue #265).
#
#   Copyright 2026
#

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from flexicon.code.BaseOperations import BaseOperations, FP_ParameterError


class _NamedLcm:
    def __init__(self, name):
        self.Name = SimpleNamespace(
            get_String=lambda _ws: SimpleNamespace(Text=name)
        )


@pytest.fixture
def ops():
    return BaseOperations(MagicMock())


class TestGuidVsNameRouting:
    def test_well_formed_guid_string_is_not_treated_as_name(self, ops):
        assert ops._IsWellFormedGuidString(
            "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        )
        assert not ops._IsWellFormedGuidString("number")

    def test_name_operand_requires_domain(self, ops):
        with pytest.raises(FP_ParameterError, match="owner"):
            ops.__ResolveFeatStrucOperand("person", domain=None, operand_role="feature")


class TestFeatStrucOperandDomain:
    def test_phoneme_owner_uses_phonological_domain(self, ops):
        owner = SimpleNamespace(ClassName="PhPhoneme")
        assert ops._FeatStrucOperandDomain(owner) == "phon"

    def test_msa_owner_uses_morphological_domain(self, ops):
        owner = SimpleNamespace(ClassName="MoStemMsa")
        assert ops._FeatStrucOperandDomain(owner) == "ms"


class TestFeatureNameResolution:
    def test_resolves_unique_feature_name(self, ops):
        feat = _NamedLcm("Number")
        fs = SimpleNamespace(FeaturesOC=[feat])
        ops.project = SimpleNamespace(
            lp=SimpleNamespace(MsFeatureSystemOA=fs),
            project=SimpleNamespace(DefaultAnalWs=1),
        )
        resolved = ops._ResolveFeatStrucFeatureName("number", "ms")
        assert resolved is feat

    def test_ambiguous_feature_name_raises(self, ops):
        fs = SimpleNamespace(
            FeaturesOC=[_NamedLcm("Number"), _NamedLcm("number")]
        )
        ops.project = SimpleNamespace(
            lp=SimpleNamespace(MsFeatureSystemOA=fs),
            project=SimpleNamespace(DefaultAnalWs=1),
        )
        with pytest.raises(FP_ParameterError, match="ambiguous"):
            ops._ResolveFeatStrucFeatureName("Number", "ms")


class TestValueNameResolution:
    def test_resolves_value_on_feature(self, ops):
        val = _NamedLcm("singular")
        feature = MagicMock()
        ops.project = SimpleNamespace(
            InflectionFeatures=SimpleNamespace(
                FeatureGetValues=lambda _f: [val]
            ),
            project=SimpleNamespace(DefaultAnalWs=1),
        )
        resolved = ops._ResolveFeatStrucValueName("Singular", "ms", feature)
        assert resolved is val
