#
#   test_describe_featstruc.py
#
#   Class: TestDescribeFeatStrucSpec / TestDescribeFeatStrucLabels /
#          TestDescribeFeatStrucObjects
#          Offline unit coverage for
#          InflectionFeatureOperations.DescribeFeatStruc (issue #557): the
#          display-only renderer for the GUID-keyed specs the #544 MSA
#          feature getters return.
#
#   The pythonnet casts (IFsSymFeatVal / IFsFeatDefn) are swapped for
#   identity functions on the module, project.Object is a dict lookup, and
#   the BaseOperations feature-struct seams (_ResolveFeatureStrucOwner /
#   _GetFeatureStruc) are monkeypatched, so no live project is needed.
#   Live coverage against real Sena 3 MSAs is in
#   test_describe_featstruc_live.py.
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
    """InflectionFeatureOperations has module-level `from SIL.LCModel
    import ...` statements that ERROR (not skip) without FieldWorks."""
    pytest.importorskip("SIL.LCModel")


# Well-formed GUIDs so the GUID-vs-name routing treats them as GUIDs.
NC_GUID = "11111111-1111-1111-1111-111111111111"
V12_GUID = "22222222-2222-2222-2222-222222222222"
NUM_GUID = "33333333-3333-3333-3333-333333333333"
SG_GUID = "44444444-4444-4444-4444-444444444444"
AGR_GUID = "55555555-5555-5555-5555-555555555555"
PERS_GUID = "66666666-6666-6666-6666-666666666666"
P3_GUID = "77777777-7777-7777-7777-777777777777"
PL_GUID = "88888888-8888-8888-8888-888888888888"
NONAME_GUID = "99999999-9999-9999-9999-999999999999"
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
    NC_GUID: _lcm("FsClosedFeature", "nc", "noun class"),
    V12_GUID: _lcm("FsSymFeatVal", "1/2", "class 1/2"),
    NUM_GUID: _lcm("FsClosedFeature", "num", "number"),
    SG_GUID: _lcm("FsSymFeatVal", "sg", "singular"),
    AGR_GUID: _lcm("FsComplexFeature", "agr", "agreement"),
    PERS_GUID: _lcm("FsClosedFeature", "pers", "person"),
    P3_GUID: _lcm("FsSymFeatVal", "3", "third"),
    PL_GUID: _lcm("FsSymFeatVal", "pl", "plural"),
    # No abbreviation: FLEx's "***" null marker must fall back to Name.
    NONAME_GUID: _lcm("FsSymFeatVal", "***", "dual"),
    # HVO key, as MakeFeatStruc also accepts.
    4242: _lcm("FsClosedFeature", "gen", "gender"),
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
    import flexicon.code.Grammar.InflectionFeatureOperations as mod

    identity = lambda obj: obj
    monkeypatch.setattr(mod, "IFsSymFeatVal", identity)
    monkeypatch.setattr(mod, "IFsFeatDefn", identity)
    return mod.InflectionFeatureOperations(_FakeProject())


# ============================================================================
# Spec-dict input (the #544 getter shape)
# ============================================================================


class TestDescribeFeatStrucSpec:
    def test_none_returns_empty_string(self, ops):
        assert ops.DescribeFeatStruc(None) == ""

    def test_empty_spec_returns_empty_brackets(self, ops):
        assert ops.DescribeFeatStruc({}) == "[]"

    def test_simple_spec_uses_abbreviations_in_order(self, ops):
        spec = {NC_GUID: V12_GUID, NUM_GUID: SG_GUID}
        assert ops.DescribeFeatStruc(spec) == "[nc: 1/2; num: sg]"

    def test_nested_complex_value_is_bracketed(self, ops):
        spec = {AGR_GUID: {PERS_GUID: P3_GUID, NUM_GUID: PL_GUID}}
        assert ops.DescribeFeatStruc(spec) == "[agr: [pers: 3; num: pl]]"

    def test_mixed_closed_and_nested(self, ops):
        spec = {NC_GUID: V12_GUID, AGR_GUID: {PERS_GUID: P3_GUID}}
        assert ops.DescribeFeatStruc(spec) == "[nc: 1/2; agr: [pers: 3]]"

    def test_empty_nested_level_renders_empty_brackets(self, ops):
        assert ops.DescribeFeatStruc({AGR_GUID: {}}) == "[agr: []]"

    def test_c4_sync_shape_is_accepted_at_every_level(self, ops):
        c4 = {
            "TypeGuid": None,
            "specs": {
                NC_GUID: V12_GUID,
                AGR_GUID: {
                    "TypeGuid": "type-guid",
                    "Guid": "nested-struct-guid",
                    "specs": {PERS_GUID: P3_GUID},
                },
            },
        }
        assert ops.DescribeFeatStruc(c4) == "[nc: 1/2; agr: [pers: 3]]"


# ============================================================================
# Label fallbacks
# ============================================================================


class TestDescribeFeatStrucLabels:
    def test_null_marker_abbreviation_falls_back_to_name(self, ops):
        assert ops.DescribeFeatStruc({NUM_GUID: NONAME_GUID}) == "[num: dual]"

    def test_stale_guid_shows_raw_guid_not_dropped(self, ops):
        assert (
            ops.DescribeFeatStruc({NUM_GUID: STALE_GUID})
            == f"[num: {STALE_GUID}]"
        )

    def test_plain_name_operands_pass_through(self, ops):
        assert ops.DescribeFeatStruc({"number": "plural"}) == "[number: plural]"

    def test_hvo_key_is_resolved(self, ops):
        assert ops.DescribeFeatStruc({4242: SG_GUID}) == "[gen: sg]"

    def test_unresolvable_hvo_shows_raw_number(self, ops):
        assert ops.DescribeFeatStruc({NUM_GUID: 99999}) == "[num: 99999]"

    def test_lcm_object_keys_are_labelled_directly(self, ops):
        spec = {OBJECTS[NUM_GUID]: OBJECTS[PL_GUID]}
        assert ops.DescribeFeatStruc(spec) == "[num: pl]"

    def test_wrapper_keys_are_unwrapped(self, ops):
        feat = _Obj(_obj=OBJECTS[NUM_GUID])
        val = _Obj(_obj=OBJECTS[SG_GUID])
        assert ops.DescribeFeatStruc({feat: val}) == "[num: sg]"


# ============================================================================
# IFsFeatStruc / owner input
# ============================================================================


class TestDescribeFeatStrucObjects:
    def test_feat_struc_is_serialized_then_described(self, ops, monkeypatch):
        from flexicon.code.Grammar.InflectionFeatureOperations import (
            InflectionFeatureOperations,
        )

        struct = SimpleNamespace(ClassName="FsFeatStruc")
        seen = []

        def fake_get(self, s):
            seen.append(s)
            return {"TypeGuid": None, "specs": {NUM_GUID: SG_GUID}}

        monkeypatch.setattr(InflectionFeatureOperations, "_GetFeatureStruc", fake_get)
        assert ops.DescribeFeatStruc(struct) == "[num: sg]"
        assert seen == [struct]

    def test_owner_reads_its_owning_property_with_slot(self, ops, monkeypatch):
        from flexicon.code.Grammar.InflectionFeatureOperations import (
            InflectionFeatureOperations,
        )

        struct = object()
        owner = SimpleNamespace(ClassName="MoDerivAffMsa", ToMsFeaturesOA=struct)
        calls = []

        def fake_resolve(self, o, slot=None):
            calls.append((o, slot))
            return o, "ToMsFeaturesOA"

        def fake_get(self, s):
            assert s is struct
            return {"TypeGuid": None, "specs": {NC_GUID: V12_GUID}}

        monkeypatch.setattr(
            InflectionFeatureOperations, "_ResolveFeatureStrucOwner", fake_resolve
        )
        monkeypatch.setattr(InflectionFeatureOperations, "_GetFeatureStruc", fake_get)

        assert ops.DescribeFeatStruc(owner, slot="To") == "[nc: 1/2]"
        assert calls == [(owner, "To")]

    def test_owner_with_null_struct_returns_empty_string(self, ops, monkeypatch):
        from flexicon.code.Grammar.InflectionFeatureOperations import (
            InflectionFeatureOperations,
        )

        owner = SimpleNamespace(ClassName="MoStemMsa", MsFeaturesOA=None)
        monkeypatch.setattr(
            InflectionFeatureOperations,
            "_ResolveFeatureStrucOwner",
            lambda self, o, slot=None: (o, "MsFeaturesOA"),
        )
        # Real _GetFeatureStruc: None in, None out -- no LCM touched.
        assert ops.DescribeFeatStruc(owner) == ""

    def test_empty_feat_struc_returns_empty_brackets(self, ops, monkeypatch):
        from flexicon.code.Grammar.InflectionFeatureOperations import (
            InflectionFeatureOperations,
        )

        monkeypatch.setattr(
            InflectionFeatureOperations,
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
