#
#   test_describe_phonfeatstruc.py
#
#   Class: TestDescribePhonFeatStrucSpec / TestDescribePhonFeatStrucLabels /
#          TestDescribePhonFeatStrucObjects / TestGetFeatureSpecs /
#          TestGetCodeRepresentation
#          Offline unit coverage for the issue #578 wrappers:
#          PhonFeatureOperations.DescribeFeatStruc,
#          PhonFeatureOperations.GetFeatureSpecs, and
#          PhonemeOperations.GetCodeRepresentation.
#
#   The pythonnet casts (IFsSymFeatVal / IFsFeatDefn / IFsClosedValue /
#   IFsClosedFeature / IFsCode / ITsString) are swapped for identity
#   functions on the module, project.Object is a dict lookup, and the
#   BaseOperations feature-struct seams (_ResolveFeatureStrucOwner /
#   _GetFeatureStruc) are monkeypatched, so no live project is needed.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

from types import SimpleNamespace

import pytest


@pytest.fixture(autouse=True)
def _require_lcmodel():
    """The operations modules have module-level `from SIL.LCModel
    import ...` statements that ERROR (not skip) without FieldWorks."""
    pytest.importorskip("SIL.LCModel")


# Well-formed GUIDs so the GUID-vs-name routing treats them as GUIDs.
CONS_GUID = "11111111-1111-1111-1111-111111111111"
PLUS_GUID = "22222222-2222-2222-2222-222222222222"
VOICE_GUID = "33333333-3333-3333-3333-333333333333"
MINUS_GUID = "44444444-4444-4444-4444-444444444444"
PLACE_GUID = "55555555-5555-5555-5555-555555555555"
CORONAL_GUID = "66666666-6666-6666-6666-666666666666"
NONAME_GUID = "77777777-7777-7777-7777-777777777777"
STALE_GUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def _multi(text):
    return SimpleNamespace(BestAnalysisAlternative=SimpleNamespace(Text=text))


class _Obj:
    """Hashable attribute bag -- spec keys may be LCM objects/wrappers,
    and SimpleNamespace is unhashable."""

    def __init__(self, **attrs):
        self.__dict__.update(attrs)


def _lcm(class_name, abbr, name):
    return _Obj(ClassName=class_name, Abbreviation=_multi(abbr), Name=_multi(name))


OBJECTS = {
    CONS_GUID: _lcm("FsClosedFeature", "cons", "consonantal"),
    PLUS_GUID: _lcm("FsSymFeatVal", "+", "plus"),
    VOICE_GUID: _lcm("FsClosedFeature", "voice", "voice"),
    MINUS_GUID: _lcm("FsSymFeatVal", "-", "minus"),
    PLACE_GUID: _lcm("FsComplexFeature", "place", "place of articulation"),
    CORONAL_GUID: _lcm("FsClosedFeature", "coronal", "coronal"),
    # No abbreviation: FLEx's "***" null marker must fall back to Name.
    NONAME_GUID: _lcm("FsSymFeatVal", "***", "sonorant-plus"),
    # HVO key, as MakeFeatStruc also accepts.
    4242: _lcm("FsClosedFeature", "nas", "nasal"),
}


class _FakeProject:
    writeEnabled = False

    def Object(self, key):
        from flexicon.code.FLExProject import FP_ParameterError

        try:
            return OBJECTS[key]
        except KeyError:
            raise FP_ParameterError(f"cannot resolve {key!r}")


@pytest.fixture
def ops(monkeypatch):
    import flexicon.code.Grammar.PhonFeatureOperations as mod

    identity = lambda obj: obj
    monkeypatch.setattr(mod, "IFsSymFeatVal", identity)
    monkeypatch.setattr(mod, "IFsFeatDefn", identity)
    monkeypatch.setattr(mod, "IFsClosedValue", identity)
    monkeypatch.setattr(mod, "IFsClosedFeature", identity)
    monkeypatch.setattr(mod, "cast_to_concrete", identity)
    return mod.PhonFeatureOperations(_FakeProject())


# ============================================================================
# DescribeFeatStruc -- spec-dict input
# ============================================================================


class TestDescribePhonFeatStrucSpec:
    def test_none_returns_empty_string(self, ops):
        assert ops.DescribeFeatStruc(None) == ""

    def test_empty_spec_returns_empty_brackets(self, ops):
        assert ops.DescribeFeatStruc({}) == "[]"

    def test_simple_spec_uses_abbreviations_in_order(self, ops):
        spec = {CONS_GUID: PLUS_GUID, VOICE_GUID: MINUS_GUID}
        assert ops.DescribeFeatStruc(spec) == "[cons: +; voice: -]"

    def test_nested_complex_value_is_bracketed(self, ops):
        spec = {PLACE_GUID: {CORONAL_GUID: PLUS_GUID}}
        assert ops.DescribeFeatStruc(spec) == "[place: [coronal: +]]"

    def test_empty_nested_level_renders_empty_brackets(self, ops):
        assert ops.DescribeFeatStruc({PLACE_GUID: {}}) == "[place: []]"

    def test_c4_sync_shape_is_accepted_at_every_level(self, ops):
        c4 = {
            "TypeGuid": None,
            "specs": {
                CONS_GUID: PLUS_GUID,
                PLACE_GUID: {
                    "TypeGuid": "type-guid",
                    "Guid": "nested-struct-guid",
                    "specs": {CORONAL_GUID: PLUS_GUID},
                },
            },
        }
        assert ops.DescribeFeatStruc(c4) == "[cons: +; place: [coronal: +]]"

    def test_bare_complex_feature_named_specs_keeps_label(self, ops):
        assert ops.DescribeFeatStruc({"specs": {"voice": "minus"}}) == (
            "[specs: [voice: minus]]"
        )


# ============================================================================
# DescribeFeatStruc -- label fallbacks
# ============================================================================


class TestDescribePhonFeatStrucLabels:
    def test_null_marker_abbreviation_falls_back_to_name(self, ops):
        assert ops.DescribeFeatStruc({VOICE_GUID: NONAME_GUID}) == (
            "[voice: sonorant-plus]"
        )

    def test_stale_guid_shows_raw_guid_not_dropped(self, ops):
        assert (
            ops.DescribeFeatStruc({VOICE_GUID: STALE_GUID})
            == f"[voice: {STALE_GUID}]"
        )

    def test_plain_name_operands_pass_through(self, ops):
        assert ops.DescribeFeatStruc({"voice": "minus"}) == "[voice: minus]"

    def test_hvo_key_is_resolved(self, ops):
        assert ops.DescribeFeatStruc({4242: PLUS_GUID}) == "[nas: +]"

    def test_unresolvable_hvo_shows_raw_number(self, ops):
        assert ops.DescribeFeatStruc({VOICE_GUID: 99999}) == "[voice: 99999]"

    def test_lcm_object_keys_are_labelled_directly(self, ops):
        spec = {OBJECTS[VOICE_GUID]: OBJECTS[MINUS_GUID]}
        assert ops.DescribeFeatStruc(spec) == "[voice: -]"

    def test_wrapper_keys_are_unwrapped(self, ops):
        feat = _Obj(_obj=OBJECTS[CONS_GUID])
        val = _Obj(_obj=OBJECTS[PLUS_GUID])
        assert ops.DescribeFeatStruc({feat: val}) == "[cons: +]"


# ============================================================================
# DescribeFeatStruc -- IFsFeatStruc / owner input
# ============================================================================


class TestDescribePhonFeatStrucObjects:
    def test_feat_struc_is_serialized_then_described(self, ops, monkeypatch):
        from flexicon.code.Grammar.PhonFeatureOperations import (
            PhonFeatureOperations,
        )

        struct = SimpleNamespace(ClassName="FsFeatStruc")
        seen = []

        def fake_get(self, s):
            seen.append(s)
            return {"TypeGuid": None, "specs": {VOICE_GUID: MINUS_GUID}}

        monkeypatch.setattr(PhonFeatureOperations, "_GetFeatureStruc", fake_get)
        assert ops.DescribeFeatStruc(struct) == "[voice: -]"
        assert seen == [struct]

    def test_phoneme_owner_reads_features_oa(self, ops, monkeypatch):
        from flexicon.code.Grammar.PhonFeatureOperations import (
            PhonFeatureOperations,
        )

        struct = object()
        owner = SimpleNamespace(ClassName="PhPhoneme", FeaturesOA=struct)
        calls = []

        def fake_resolve(self, o, slot=None):
            calls.append((o, slot))
            return o, "FeaturesOA"

        def fake_get(self, s):
            assert s is struct
            return {"TypeGuid": None, "specs": {CONS_GUID: PLUS_GUID}}

        monkeypatch.setattr(
            PhonFeatureOperations, "_ResolveFeatureStrucOwner", fake_resolve
        )
        monkeypatch.setattr(PhonFeatureOperations, "_GetFeatureStruc", fake_get)

        assert ops.DescribeFeatStruc(owner) == "[cons: +]"
        assert calls == [(owner, None)]

    def test_owner_with_null_struct_returns_empty_string(self, ops, monkeypatch):
        from flexicon.code.Grammar.PhonFeatureOperations import (
            PhonFeatureOperations,
        )

        owner = SimpleNamespace(ClassName="PhPhoneme", FeaturesOA=None)
        monkeypatch.setattr(
            PhonFeatureOperations,
            "_ResolveFeatureStrucOwner",
            lambda self, o, slot=None: (o, "FeaturesOA"),
        )
        # Real _GetFeatureStruc: None in, None out -- no LCM touched.
        assert ops.DescribeFeatStruc(owner) == ""

    def test_empty_feat_struc_returns_empty_brackets(self, ops, monkeypatch):
        from flexicon.code.Grammar.PhonFeatureOperations import (
            PhonFeatureOperations,
        )

        monkeypatch.setattr(
            PhonFeatureOperations,
            "_GetFeatureStruc",
            lambda self, s: {"TypeGuid": None, "specs": {}},
        )
        struct = SimpleNamespace(ClassName="FsFeatStruc")
        assert ops.DescribeFeatStruc(struct) == "[]"

    def test_non_lcm_input_raises_parameter_error(self, ops):
        from flexicon.code.FLExProject import FP_ParameterError

        with pytest.raises(FP_ParameterError, match="DescribeFeatStruc"):
            ops.DescribeFeatStruc("not a spec")

    def test_non_owner_class_raises_parameter_error(self, ops):
        from flexicon.code.FLExProject import FP_ParameterError

        with pytest.raises(FP_ParameterError, match="not a recognized"):
            ops.DescribeFeatStruc(SimpleNamespace(ClassName="LexEntry"))


# ============================================================================
# GetFeatureSpecs -- resolved (feature, value) object pairs
# ============================================================================


def _closed_spec(feat, val):
    return SimpleNamespace(
        ClassName="FsClosedValue", FeatureRA=feat, ValueRA=val
    )


class TestGetFeatureSpecs:
    def test_none_returns_empty_list(self, ops):
        assert ops.GetFeatureSpecs(None) == []

    def test_struct_returns_feature_value_pairs(self, ops):
        cons = _lcm("FsClosedFeature", "cons", "consonantal")
        plus = _lcm("FsSymFeatVal", "+", "plus")
        voice = _lcm("FsClosedFeature", "voice", "voice")
        minus = _lcm("FsSymFeatVal", "-", "minus")
        struct = SimpleNamespace(
            ClassName="FsFeatStruc",
            FeatureSpecsOC=[_closed_spec(cons, plus), _closed_spec(voice, minus)],
        )
        assert ops.GetFeatureSpecs(struct) == [(cons, plus), (voice, minus)]

    def test_owner_resolves_via_features_oa(self, ops, monkeypatch):
        from flexicon.code.Grammar.PhonFeatureOperations import (
            PhonFeatureOperations,
        )

        cons = _lcm("FsClosedFeature", "cons", "consonantal")
        plus = _lcm("FsSymFeatVal", "+", "plus")
        struct = SimpleNamespace(
            ClassName="FsFeatStruc",
            FeatureSpecsOC=[_closed_spec(cons, plus)],
        )
        owner = SimpleNamespace(ClassName="PhPhoneme", FeaturesOA=struct)
        monkeypatch.setattr(
            PhonFeatureOperations,
            "_ResolveFeatureStrucOwner",
            lambda self, o, slot=None: (o, "FeaturesOA"),
        )
        assert ops.GetFeatureSpecs(owner) == [(cons, plus)]

    def test_owner_with_null_struct_returns_empty_list(self, ops, monkeypatch):
        from flexicon.code.Grammar.PhonFeatureOperations import (
            PhonFeatureOperations,
        )

        owner = SimpleNamespace(ClassName="PhPhoneme", FeaturesOA=None)
        monkeypatch.setattr(
            PhonFeatureOperations,
            "_ResolveFeatureStrucOwner",
            lambda self, o, slot=None: (o, "FeaturesOA"),
        )
        assert ops.GetFeatureSpecs(owner) == []

    def test_complex_and_malformed_specs_are_skipped(self, ops):
        cons = _lcm("FsClosedFeature", "cons", "consonantal")
        plus = _lcm("FsSymFeatVal", "+", "plus")
        struct = SimpleNamespace(
            ClassName="FsFeatStruc",
            FeatureSpecsOC=[
                _closed_spec(cons, plus),
                # Complex value: not an (IFsClosedFeature, IFsSymFeatVal) pair.
                SimpleNamespace(ClassName="FsComplexValue", FeatureRA=cons),
                # Malformed: null FeatureRA / ValueRA.
                SimpleNamespace(ClassName="FsClosedValue", FeatureRA=None, ValueRA=plus),
                SimpleNamespace(ClassName="FsClosedValue", FeatureRA=cons, ValueRA=None),
            ],
        )
        assert ops.GetFeatureSpecs(struct) == [(cons, plus)]

    def test_dict_input_raises_parameter_error(self, ops):
        from flexicon.code.FLExProject import FP_ParameterError

        with pytest.raises(FP_ParameterError, match="GetFeatureSpecs"):
            ops.GetFeatureSpecs({CONS_GUID: PLUS_GUID})

    def test_non_lcm_input_raises_parameter_error(self, ops):
        from flexicon.code.FLExProject import FP_ParameterError

        with pytest.raises(FP_ParameterError, match="GetFeatureSpecs"):
            ops.GetFeatureSpecs("not a struct")

    def test_non_owner_class_raises_parameter_error(self, ops):
        from flexicon.code.FLExProject import FP_ParameterError

        with pytest.raises(FP_ParameterError, match="not a recognized"):
            ops.GetFeatureSpecs(SimpleNamespace(ClassName="LexEntry"))


# ============================================================================
# PhonemeOperations.GetCodeRepresentation
# ============================================================================


class _FakeCodeProject:
    writeEnabled = False
    project = SimpleNamespace(DefaultVernWs=5)

    def Object(self, hvo):
        return _CODES_BY_HVO[hvo]


def _make_code(text):
    rep = SimpleNamespace(get_String=lambda ws: SimpleNamespace(Text=text))
    return SimpleNamespace(ClassName="PhCode", Representation=rep)


_CODES_BY_HVO = {
    101: _make_code("[tʰ]"),
    102: _make_code("***"),  # FLEx null marker -> ""
    103: _make_code(None),  # unset -> ""
}


@pytest.fixture
def code_ops(monkeypatch):
    import flexicon.code.Grammar.PhonemeOperations as mod

    identity = lambda obj: obj
    monkeypatch.setattr(mod, "ITsString", identity)
    monkeypatch.setattr(mod, "cast_to_concrete", identity)
    project = _FakeCodeProject()
    project._FLExProject__WSHandle = lambda ws, default: (
        default if ws is None else ws
    )
    return mod.PhonemeOperations(project)


class TestGetCodeRepresentation:
    def test_code_object_returns_representation(self, code_ops):
        assert code_ops.GetCodeRepresentation(_CODES_BY_HVO[101]) == "[tʰ]"

    def test_hvo_input_is_resolved(self, code_ops):
        assert code_ops.GetCodeRepresentation(101) == "[tʰ]"

    def test_null_marker_normalizes_to_empty_string(self, code_ops):
        assert code_ops.GetCodeRepresentation(_CODES_BY_HVO[102]) == ""

    def test_unset_representation_returns_empty_string(self, code_ops):
        assert code_ops.GetCodeRepresentation(_CODES_BY_HVO[103]) == ""

    def test_default_ws_is_vernacular(self, code_ops):
        seen = {}

        def get_string(ws):
            seen["ws"] = ws
            return SimpleNamespace(Text="[p]")

        code = SimpleNamespace(
            ClassName="PhCode",
            Representation=SimpleNamespace(get_String=get_string),
        )
        assert code_ops.GetCodeRepresentation(code) == "[p]"
        assert seen["ws"] == 5

    def test_explicit_ws_is_used(self, code_ops):
        seen = {}

        def get_string(ws):
            seen["ws"] = ws
            return SimpleNamespace(Text="[t]")

        code = SimpleNamespace(
            ClassName="PhCode",
            Representation=SimpleNamespace(get_String=get_string),
        )
        assert code_ops.GetCodeRepresentation(code, 7) == "[t]"
        assert seen["ws"] == 7

    def test_none_raises_null_parameter_error(self, code_ops):
        from flexicon.code.FLExProject import FP_NullParameterError

        with pytest.raises(FP_NullParameterError):
            code_ops.GetCodeRepresentation(None)
