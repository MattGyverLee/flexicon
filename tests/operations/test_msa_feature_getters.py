#
#   test_msa_feature_getters.py
#
#   Class: TestC4ToFeatStrucSpec / TestExplicitGetters / TestGetFeaturesDispatch
#          Offline unit coverage for MSAOperations' feature-structure
#          getters (issue #544): GetStemFeatures / GetInflAffFeatures /
#          GetDerivFromFeatures / GetDerivToFeatures / GetFeatures.
#
#   These are the read-side pair for
#   InflectionFeatures.MakeFeatStruc(specs, owner=msa, ...): the getters
#   must return a spec shaped so it can be fed straight back into
#   MakeFeatStruc, NOT the raw C4 sync wire-format _GetFeatureStruc
#   returns. Mirrors tests/operations/test_issue251_msa_feature_sync.py's
#   monkeypatching of the BaseOperations feature-struct seams
#   (_ResolveFeatureStrucOwner / _GetFeatureStruc) and MSAOperations' own
#   HVO/GUID resolver, so no real SIL.LCModel cast or live project is
#   required here. Live round-trip coverage (MakeFeatStruc -> getter ->
#   MakeFeatStruc again, re-read from the LCM) is in
#   test_msa_feature_getters_live.py.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest


@pytest.fixture(autouse=True)
def _require_lcmodel():
    """MSAOperations has module-level `from SIL.LCModel import ...`
    statements that ERROR (not skip) without FieldWorks installed."""
    pytest.importorskip("SIL.LCModel")


def _import_ops():
    from flexicon.code.Lexicon.MSAOperations import MSAOperations
    from flexicon.code.FLExProject import FP_ParameterError, FP_NullParameterError

    return MSAOperations, FP_ParameterError, FP_NullParameterError


class _FakeMsa:
    def __init__(self, class_name, **attrs):
        self.ClassName = class_name
        for k, v in attrs.items():
            setattr(self, k, v)


class _FakeFeatStruct:
    def __init__(self, guid):
        self.Guid = guid


class _FakeProject:
    """Every test here monkeypatches away the feature-struct seams and
    the sense_or_msa resolver, so MSAOperations never touches self.project."""

    writeEnabled = True


def _make_fake_resolver(calls, prop_by_class_and_slot):
    def _fake(self, owner, slot=None):
        calls.append((owner, slot))
        prop_name = prop_by_class_and_slot[(owner.ClassName, slot)]
        return owner, prop_name

    return _fake


_MSA_PROP_BY_CLASS_AND_SLOT = {
    ("MoStemMsa", None): "MsFeaturesOA",
    ("MoInflAffMsa", None): "InflFeatsOA",
    ("MoDerivAffMsa", "From"): "FromMsFeaturesOA",
    ("MoDerivAffMsa", "To"): "ToMsFeaturesOA",
}


def _fake_get_feature_struc_present(self, struct):
    """A struct that IS attached (non-None) -- mirrors _GetFeatureStruc's
    real C4 shape, with one closed value and one nested complex value."""
    if struct is None:
        return None
    return {
        "TypeGuid": None,
        "specs": {
            "FEAT-CLOSED-GUID": "VAL-CLOSED-GUID",
            "FEAT-COMPLEX-GUID": {
                "TypeGuid": "NESTED-TYPE-GUID",
                "Guid": "NESTED-STRUCT-GUID",
                "specs": {"FEAT-NESTED-GUID": "VAL-NESTED-GUID"},
            },
        },
    }


def _fake_get_feature_struc_empty(self, struct):
    if struct is None:
        return None
    return {"TypeGuid": None, "specs": {}}


@pytest.fixture
def msa_ops(monkeypatch):
    MSAOperations, _, _ = _import_ops()
    return MSAOperations(_FakeProject())


def _stub_resolve_msa(monkeypatch, MSAOperations, msa_or_none):
    monkeypatch.setattr(
        MSAOperations,
        "_MSAOperations__ResolveMsaForFeatures",
        lambda self, sense_or_msa: msa_or_none,
    )


# ============================================================================
# __C4ToFeatStrucSpec -- the C4 -> MakeFeatStruc shape converter
# ============================================================================


class TestC4ToFeatStrucSpec:
    def test_none_stays_none(self, msa_ops):
        convert = msa_ops._MSAOperations__C4ToFeatStrucSpec
        assert convert(None) is None

    def test_empty_specs_stays_empty_dict_not_none(self, msa_ops):
        convert = msa_ops._MSAOperations__C4ToFeatStrucSpec
        assert convert({"TypeGuid": None, "specs": {}}) == {}

    def test_closed_value_becomes_flat_guid_pair(self, msa_ops):
        convert = msa_ops._MSAOperations__C4ToFeatStrucSpec
        c4 = {"TypeGuid": None, "specs": {"FEAT": "VAL"}}
        assert convert(c4) == {"FEAT": "VAL"}

    def test_typeguid_is_dropped(self, msa_ops):
        """TypeGuid carries no info for a MakeFeatStruc round-trip (it
        never writes TypeRA back) so the converter must not surface it
        as a spec key."""
        convert = msa_ops._MSAOperations__C4ToFeatStrucSpec
        c4 = {"TypeGuid": "SOME-TYPE-GUID", "specs": {"FEAT": "VAL"}}
        result = convert(c4)
        assert "TypeGuid" not in result
        assert "TypeGuid" not in str(list(result.keys()))

    def test_nested_complex_value_recurses_and_drops_nested_guid(self, msa_ops):
        convert = msa_ops._MSAOperations__C4ToFeatStrucSpec
        c4 = {
            "TypeGuid": None,
            "specs": {
                "OUTER-FEAT": {
                    "TypeGuid": "NESTED-TYPE",
                    "Guid": "NESTED-STRUCT-GUID",
                    "specs": {"INNER-FEAT": "INNER-VAL"},
                },
            },
        }
        result = convert(c4)
        assert result == {"OUTER-FEAT": {"INNER-FEAT": "INNER-VAL"}}
        assert "Guid" not in result["OUTER-FEAT"]

    def test_converter_never_touches_a_raw_lcm_object(self, msa_ops):
        """
        Category-8 guard (triggered by a live-run investigation of a
        missing IFsFeatStruc(...) cast found in this file's own live
        test assertion, NOT in library code): __C4ToFeatStrucSpec must
        operate ONLY on the already-serialized C4 dict that
        _GetFeatureStruc hands it -- never on a raw LCM
        ValueOA/IFsAbstractStructure that would need its own explicit
        cast before FeatureSpecsOC is reachable. Prove it by handing the
        converter a nested "value" that is a dict with no LCM-style
        attributes at all (no .FeatureSpecsOC, no .Guid attribute
        access attempted) and confirming it still recurses correctly
        via plain dict indexing.
        """
        convert = msa_ops._MSAOperations__C4ToFeatStrucSpec

        class _NotAnLcmObject:
            """No .FeatureSpecsOC, no .Guid -- if the converter ever
            attribute-accessed this instead of dict-indexing it, this
            would raise AttributeError exactly like the live failure."""

            def __getattr__(self, name):
                raise AttributeError(
                    f"converter must never attribute-access {name!r} on "
                    f"a nested value -- it only walks dict keys"
                )

        # The nested C4 level is itself a dict (as _GetFeatureStruc
        # always produces); the sentinel proves nothing SIBLING to it
        # is ever touched via attribute access.
        c4 = {
            "TypeGuid": None,
            "specs": {
                "OUTER-FEAT": {
                    "TypeGuid": None,
                    "Guid": "NESTED-GUID",
                    "specs": {"INNER-FEAT": "INNER-VAL"},
                },
            },
            "_sentinel": _NotAnLcmObject(),
        }
        result = convert(c4)
        assert result == {"OUTER-FEAT": {"INNER-FEAT": "INNER-VAL"}}


# ============================================================================
# Explicit per-class getters
# ============================================================================


class TestExplicitGetters:
    def test_get_stem_features_present_struct_round_trip_shape(
        self, monkeypatch, msa_ops
    ):
        MSAOperations, _, _ = _import_ops()
        calls = []
        monkeypatch.setattr(
            MSAOperations,
            "_ResolveFeatureStrucOwner",
            _make_fake_resolver(calls, _MSA_PROP_BY_CLASS_AND_SLOT),
        )
        monkeypatch.setattr(
            MSAOperations, "_GetFeatureStruc", _fake_get_feature_struc_present
        )
        msa = _FakeMsa("MoStemMsa", MsFeaturesOA=_FakeFeatStruct("g1"))
        _stub_resolve_msa(monkeypatch, MSAOperations, msa)

        spec = msa_ops.GetStemFeatures(msa)

        assert calls == [(msa, None)]
        assert spec == {
            "FEAT-CLOSED-GUID": "VAL-CLOSED-GUID",
            "FEAT-COMPLEX-GUID": {"FEAT-NESTED-GUID": "VAL-NESTED-GUID"},
        }

    def test_get_stem_features_null_struct_is_none(self, monkeypatch, msa_ops):
        MSAOperations, _, _ = _import_ops()
        monkeypatch.setattr(
            MSAOperations,
            "_ResolveFeatureStrucOwner",
            _make_fake_resolver([], _MSA_PROP_BY_CLASS_AND_SLOT),
        )
        monkeypatch.setattr(
            MSAOperations, "_GetFeatureStruc", _fake_get_feature_struc_present
        )
        msa = _FakeMsa("MoStemMsa", MsFeaturesOA=None)
        _stub_resolve_msa(monkeypatch, MSAOperations, msa)

        assert msa_ops.GetStemFeatures(msa) is None

    def test_get_stem_features_present_empty_struct_is_empty_dict(
        self, monkeypatch, msa_ops
    ):
        MSAOperations, _, _ = _import_ops()
        monkeypatch.setattr(
            MSAOperations,
            "_ResolveFeatureStrucOwner",
            _make_fake_resolver([], _MSA_PROP_BY_CLASS_AND_SLOT),
        )
        monkeypatch.setattr(
            MSAOperations, "_GetFeatureStruc", _fake_get_feature_struc_empty
        )
        msa = _FakeMsa("MoStemMsa", MsFeaturesOA=_FakeFeatStruct("g1"))
        _stub_resolve_msa(monkeypatch, MSAOperations, msa)

        assert msa_ops.GetStemFeatures(msa) == {}

    def test_get_stem_features_wrong_class_is_none_not_raise(
        self, monkeypatch, msa_ops
    ):
        MSAOperations, _, _ = _import_ops()

        def _resolver_must_not_be_called(self, owner, slot=None):
            raise AssertionError(
                "GetStemFeatures must discriminate on ClassName BEFORE "
                "ever calling _ResolveFeatureStrucOwner for a mismatched "
                "MSA (mirrors GetInflAffMsaSlots's graceful non-raise)."
            )

        monkeypatch.setattr(
            MSAOperations, "_ResolveFeatureStrucOwner", _resolver_must_not_be_called
        )
        msa = _FakeMsa("MoInflAffMsa", InflFeatsOA=None)
        _stub_resolve_msa(monkeypatch, MSAOperations, msa)

        assert msa_ops.GetStemFeatures(msa) is None

    def test_get_infl_aff_features_present(self, monkeypatch, msa_ops):
        MSAOperations, _, _ = _import_ops()
        monkeypatch.setattr(
            MSAOperations,
            "_ResolveFeatureStrucOwner",
            _make_fake_resolver([], _MSA_PROP_BY_CLASS_AND_SLOT),
        )
        monkeypatch.setattr(
            MSAOperations, "_GetFeatureStruc", _fake_get_feature_struc_present
        )
        msa = _FakeMsa("MoInflAffMsa", InflFeatsOA=_FakeFeatStruct("g1"))
        _stub_resolve_msa(monkeypatch, MSAOperations, msa)

        spec = msa_ops.GetInflAffFeatures(msa)

        assert spec["FEAT-CLOSED-GUID"] == "VAL-CLOSED-GUID"

    def test_get_deriv_from_features_uses_from_slot(self, monkeypatch, msa_ops):
        MSAOperations, _, _ = _import_ops()
        calls = []
        monkeypatch.setattr(
            MSAOperations,
            "_ResolveFeatureStrucOwner",
            _make_fake_resolver(calls, _MSA_PROP_BY_CLASS_AND_SLOT),
        )
        monkeypatch.setattr(
            MSAOperations, "_GetFeatureStruc", _fake_get_feature_struc_present
        )
        msa = _FakeMsa(
            "MoDerivAffMsa",
            FromMsFeaturesOA=_FakeFeatStruct("g1"),
            ToMsFeaturesOA=None,
        )
        _stub_resolve_msa(monkeypatch, MSAOperations, msa)

        msa_ops.GetDerivFromFeatures(msa)

        assert calls == [(msa, "From")]

    def test_get_deriv_to_features_uses_to_slot(self, monkeypatch, msa_ops):
        MSAOperations, _, _ = _import_ops()
        calls = []
        monkeypatch.setattr(
            MSAOperations,
            "_ResolveFeatureStrucOwner",
            _make_fake_resolver(calls, _MSA_PROP_BY_CLASS_AND_SLOT),
        )
        monkeypatch.setattr(
            MSAOperations, "_GetFeatureStruc", _fake_get_feature_struc_present
        )
        msa = _FakeMsa(
            "MoDerivAffMsa",
            FromMsFeaturesOA=None,
            ToMsFeaturesOA=_FakeFeatStruct("g2"),
        )
        _stub_resolve_msa(monkeypatch, MSAOperations, msa)

        msa_ops.GetDerivToFeatures(msa)

        assert calls == [(msa, "To")]

    def test_sense_with_no_msa_is_none(self, monkeypatch, msa_ops):
        MSAOperations, _, _ = _import_ops()
        _stub_resolve_msa(monkeypatch, MSAOperations, None)

        assert msa_ops.GetStemFeatures(object()) is None
        assert msa_ops.GetInflAffFeatures(object()) is None
        assert msa_ops.GetDerivFromFeatures(object()) is None
        assert msa_ops.GetDerivToFeatures(object()) is None
        assert msa_ops.GetFeatures(object()) is None

    def test_null_param_raises(self, msa_ops):
        _, _, FP_NullParameterError = _import_ops()
        with pytest.raises(FP_NullParameterError):
            msa_ops.GetStemFeatures(None)
        with pytest.raises(FP_NullParameterError):
            msa_ops.GetFeatures(None)


# ============================================================================
# GetFeatures dispatch
# ============================================================================


class TestGetFeaturesDispatch:
    def test_dispatches_stem_msa_to_ms_features(self, monkeypatch, msa_ops):
        MSAOperations, _, _ = _import_ops()
        calls = []
        monkeypatch.setattr(
            MSAOperations,
            "_ResolveFeatureStrucOwner",
            _make_fake_resolver(calls, _MSA_PROP_BY_CLASS_AND_SLOT),
        )
        monkeypatch.setattr(
            MSAOperations, "_GetFeatureStruc", _fake_get_feature_struc_present
        )
        msa = _FakeMsa("MoStemMsa", MsFeaturesOA=_FakeFeatStruct("g1"))
        _stub_resolve_msa(monkeypatch, MSAOperations, msa)

        spec = msa_ops.GetFeatures(msa)

        assert calls == [(msa, None)]
        assert spec["FEAT-CLOSED-GUID"] == "VAL-CLOSED-GUID"

    def test_dispatches_infl_aff_msa(self, monkeypatch, msa_ops):
        MSAOperations, _, _ = _import_ops()
        calls = []
        monkeypatch.setattr(
            MSAOperations,
            "_ResolveFeatureStrucOwner",
            _make_fake_resolver(calls, _MSA_PROP_BY_CLASS_AND_SLOT),
        )
        monkeypatch.setattr(
            MSAOperations, "_GetFeatureStruc", _fake_get_feature_struc_present
        )
        msa = _FakeMsa("MoInflAffMsa", InflFeatsOA=_FakeFeatStruct("g1"))
        _stub_resolve_msa(monkeypatch, MSAOperations, msa)

        msa_ops.GetFeatures(msa)

        assert calls == [(msa, None)]

    def test_deriv_aff_msa_with_slot_from(self, monkeypatch, msa_ops):
        MSAOperations, _, _ = _import_ops()
        calls = []
        monkeypatch.setattr(
            MSAOperations,
            "_ResolveFeatureStrucOwner",
            _make_fake_resolver(calls, _MSA_PROP_BY_CLASS_AND_SLOT),
        )
        monkeypatch.setattr(
            MSAOperations, "_GetFeatureStruc", _fake_get_feature_struc_present
        )
        msa = _FakeMsa(
            "MoDerivAffMsa",
            FromMsFeaturesOA=_FakeFeatStruct("g1"),
            ToMsFeaturesOA=None,
        )
        _stub_resolve_msa(monkeypatch, MSAOperations, msa)

        msa_ops.GetFeatures(msa, slot="From")

        assert calls == [(msa, "From")]

    def test_deriv_aff_msa_without_slot_raises(self, monkeypatch, msa_ops):
        """Never guess between From/To -- FP_ParameterError, matching
        _ResolveFeatureStrucOwner's own ambiguous-ClassName policy."""
        MSAOperations, FP_ParameterError, _ = _import_ops()

        def _resolver_must_not_be_called(self, owner, slot=None):
            raise AssertionError(
                "GetFeatures must raise on a missing slot= for "
                "MoDerivAffMsa BEFORE ever calling _ResolveFeatureStrucOwner."
            )

        monkeypatch.setattr(
            MSAOperations, "_ResolveFeatureStrucOwner", _resolver_must_not_be_called
        )
        msa = _FakeMsa("MoDerivAffMsa", FromMsFeaturesOA=None, ToMsFeaturesOA=None)
        _stub_resolve_msa(monkeypatch, MSAOperations, msa)

        with pytest.raises(FP_ParameterError):
            msa_ops.GetFeatures(msa)

    def test_deriv_aff_msa_with_invalid_slot_raises(self, monkeypatch, msa_ops):
        MSAOperations, FP_ParameterError, _ = _import_ops()
        msa = _FakeMsa("MoDerivAffMsa", FromMsFeaturesOA=None, ToMsFeaturesOA=None)
        _stub_resolve_msa(monkeypatch, MSAOperations, msa)

        with pytest.raises(FP_ParameterError):
            msa_ops.GetFeatures(msa, slot="Sideways")

    def test_unclassified_affix_msa_is_none(self, monkeypatch, msa_ops):
        MSAOperations, _, _ = _import_ops()

        def _resolver_must_not_be_called(self, owner, slot=None):
            raise AssertionError(
                "MoUnclassifiedAffixMsa carries no feature-struct "
                "property; the resolver must never be consulted for it."
            )

        monkeypatch.setattr(
            MSAOperations, "_ResolveFeatureStrucOwner", _resolver_must_not_be_called
        )
        msa = _FakeMsa("MoUnclassifiedAffixMsa")
        _stub_resolve_msa(monkeypatch, MSAOperations, msa)

        assert msa_ops.GetFeatures(msa) is None

    def test_out_of_table_class_name_is_none(self, monkeypatch, msa_ops):
        MSAOperations, _, _ = _import_ops()
        msa = _FakeMsa("MoDerivStepMsa")
        _stub_resolve_msa(monkeypatch, MSAOperations, msa)

        assert msa_ops.GetFeatures(msa) is None
