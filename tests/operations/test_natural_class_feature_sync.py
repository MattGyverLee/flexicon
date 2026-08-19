#
#   test_natural_class_feature_sync.py
#
#   Class: TestNaturalClassSyncStatic
#          Static source-pattern locks for the FeaturesOA cross-project
#          sync fix in NaturalClassOperations (the natural-class sibling
#          of PhonemeOperations issue #222). Mirrors
#          TestSyncTypeCorrectionsStatic in test_apply_syncable_properties.py:
#          these tests import the real module and inspect method source via
#          `inspect.getsource`, but never open a FieldWorks project, so they
#          run on any machine with FieldWorks/SIL.LCModel installed
#          (no `requires_live_project` marker, no live .fwdata needed).
#
#   Context: NaturalClassOperations.GetSyncableProperties previously
#   returned only Name/Abbreviation/Description/PhonemeGuids for every
#   natural class -- for a feature-based IPhNCFeatures item, its owned
#   FeaturesOA (the whole point of the object) was never captured, and
#   ApplySyncableProperties purely delegated to BaseOperations with no
#   Features handling whatsoever. Every feature-based natural class
#   therefore synced across with a correct Name/GUID but a null
#   FeaturesOA -- rules referencing the class silently matched nothing.
#   These tests lock:
#     (1) GetSyncableProperties surfaces FeaturesGuid + Features for
#         IPhNCFeatures, via FeatureSpecsOC (not just the old four keys).
#     (2) ApplySyncableProperties/​__ApplyFeatures RAISE (FP_ParameterError)
#         on an unresolved feature/value GUID rather than silently
#         `continue`-ing past it (which is the exact silence being fixed).
#     (3) The segment-based (PhonemeGuids) path is untouched.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import inspect

import pytest


@pytest.fixture(autouse=True)
def _require_lcmodel():
    """
    NaturalClassOperations has module-level `from SIL.LCModel import ...`
    statements. On a machine without FieldWorks installed, that import
    ERRORs rather than skipping cleanly -- so skip explicitly instead.
    Importing the module (and even calling FLExInitialize elsewhere) does
    NOT open any .fwdata project; these tests never touch a live project.
    """
    pytest.importorskip("SIL.LCModel")


def _method_source(method_name):
    from flexicon.code.Grammar.NaturalClassOperations import (
        NaturalClassOperations,
    )

    obj = NaturalClassOperations.__dict__[method_name]

    seen = set()
    while True:
        oid = id(obj)
        if oid in seen:
            break
        seen.add(oid)
        if hasattr(obj, "func") and not inspect.isfunction(obj):
            obj = obj.func
            continue
        if hasattr(obj, "__wrapped__"):
            obj = obj.__wrapped__
            continue
        break

    return inspect.getsource(obj)


class TestNaturalClassSyncStatic:
    """Locks the shape of the FeaturesOA sync fix without a live project."""

    def test_getsyncable_properties_emits_features_guid_and_specs(self):
        src = _method_source("GetSyncableProperties")

        assert 'props["FeaturesGuid"] = str(features.Guid)' in src, (
            "GetSyncableProperties must capture the owned IFsFeatStruc's "
            "GUID under 'FeaturesGuid' for feature-based (IPhNCFeatures) "
            "natural classes, mirroring PhonemeOperations issue #222."
        )
        assert '"FeatureGuid"' in src and '"ValueGuid"' in src, (
            "GetSyncableProperties must emit {'FeatureGuid', 'ValueGuid'} "
            "spec dicts -- without this, a synced feature-based natural "
            "class carries no feature-value constraints at all."
        )
        assert "FeatureSpecsOC" in src, (
            "GetSyncableProperties must walk FeaturesOA.FeatureSpecsOC to "
            "build the Features list."
        )

    def test_getsyncable_properties_still_emits_phoneme_guids(self):
        """
        The PhNCSegments / PhonemeGuids path must be untouched by the
        FeaturesOA fix -- segment-based classes already synced correctly.
        """
        src = _method_source("GetSyncableProperties")
        assert '"PhonemeGuids"' in src
        assert "SegmentsRC" in src

    def test_apply_syncable_properties_delegates_features_to_helper(self):
        src = _method_source("ApplySyncableProperties")
        assert "__ApplyFeatures" in src, (
            "ApplySyncableProperties must no longer be a pure "
            "super().ApplySyncableProperties(...) delegation -- it must "
            "dispatch Features/FeaturesGuid to a dedicated handler, the "
            "same shape as PhonemeOperations.ApplySyncableProperties."
        )

    def test_apply_features_raises_on_unresolved_feature_guid(self):
        """
        Pins the core behavioral requirement: an unresolved feature GUID
        must raise FP_ParameterError, not `continue`/`pass` past it. This
        is the opposite of PhonemeOperations.__ApplyFeatures, which skips
        silently -- silence is exactly the natural-class bug being fixed,
        so the two must NOT share that behavior.
        """
        src = _method_source("_NaturalClassOperations__ApplyFeatures")

        assert "raise FP_ParameterError" in src, (
            "__ApplyFeatures must raise FP_ParameterError when a feature "
            "or value GUID does not resolve in the target project."
        )
        assert "feat_obj is None" in src and "raise" in src, (
            "A None feat_obj (unresolved FeatureGuid) must be checked "
            "and raised on, not silently skipped."
        )
        assert "val_obj is None" in src, (
            "A None val_obj (unresolved ValueGuid) must be checked and "
            "raised on, not silently skipped."
        )

        # Negative check: guard against reintroducing the phoneme-style
        # silent-skip idiom for the "not found" branches specifically.
        # (A bare `continue` still legitimately appears for the
        # already-applied/idempotency branch a few lines earlier -- this
        # only pins that the *unresolved-GUID* branches raise.)
        unresolved_section = src[src.index("feat_obj = self.__ResolveByGuid") :]
        assert "continue" not in unresolved_section.split("val_obj = self.__ResolveByGuid")[0], (
            "The unresolved-FeatureGuid branch must raise, not `continue`."
        )

    def test_apply_features_error_message_names_guid_and_class(self):
        src = _method_source("_NaturalClassOperations__ApplyFeatures")
        assert "{feat_guid}" in src or "feat_guid}" in src, (
            "The raised exception message must name the missing "
            "FeatureGuid so the failure is actionable."
        )
        assert "{nc_name}" in src or "nc_name}" in src, (
            "The raised exception message must name the natural class "
            "so the failure is actionable."
        )

    def test_apply_syncable_properties_raises_on_type_mismatch(self):
        src = _method_source("ApplySyncableProperties")
        assert 'nc.ClassName != "PhNCFeatures"' in src, (
            "ApplySyncableProperties must detect a Features/segments type "
            "mismatch (source carries Features, target item isn't "
            "feature-based) by checking nc.ClassName -- NOT "
            "hasattr(nc, 'FeaturesOA'), which is always False for a "
            "base-IPhNaturalClass-typed object under pythonnet even when "
            "the underlying object really is PhNCFeatures (see "
            "TestNaturalClassSyncPythonnetBaseInterfaceView below)."
        )

    def test_no_hasattr_gate_on_subtype_only_members(self):
        """
        Regression lock for the 2026-08-19 live-verification failure: the
        original fix gated on hasattr(nc, "FeaturesOA") /
        hasattr(nc, "SegmentsRC"), which is silently always False for
        objects returned by GetAll()/Find()/Object() (pythonnet exposes
        only the STATIC wrapper interface -- base IPhNaturalClass -- not
        the runtime CLR subtype). That made the entire fix dead code
        against live data despite passing every purely-static test that
        existed at the time. Source must no longer contain either hasattr
        gate anywhere in these three methods; discrimination must go
        through .ClassName instead.
        """
        get_src = _method_source("GetSyncableProperties")
        apply_src = _method_source("ApplySyncableProperties")
        apply_features_src = _method_source(
            "_NaturalClassOperations__ApplyFeatures"
        )

        # Match the actual GATING idiom ("if [not ]hasattr(nc, ...)"), not
        # bare mentions of hasattr(nc, "FeaturesOA") inside explanatory
        # comments/docstrings describing *why* the fix avoids it -- those
        # mentions are expected and desirable documentation.
        gate_patterns = (
            'if hasattr(nc, "FeaturesOA")',
            'if not hasattr(nc, "FeaturesOA")',
            'if hasattr(nc, "SegmentsRC")',
            'if not hasattr(nc, "SegmentsRC")',
        )
        for src, label in (
            (get_src, "GetSyncableProperties"),
            (apply_src, "ApplySyncableProperties"),
            (apply_features_src, "__ApplyFeatures"),
        ):
            for pattern in gate_patterns:
                assert pattern not in src, (
                    f"{label} must not gate with `{pattern}` -- "
                    "hasattr(nc, ...) on a subtype-only member (FeaturesOA/"
                    "SegmentsRC) is always False for a base-"
                    "IPhNaturalClass-typed object under pythonnet, even "
                    "for a genuine PhNCFeatures/PhNCSegments item. "
                    "Verified live against Ngoreme FLEx (41/41 "
                    "PhNCFeatures and 7/7 PhNCSegments failed this "
                    "hasattr check)."
                )

        assert "nc.ClassName" in get_src, (
            "GetSyncableProperties must discriminate PhNCSegments vs "
            "PhNCFeatures via .ClassName (reliably visible on the base "
            "interface), not via hasattr on a subtype-only member."
        )


class _FakeTsString:
    """Stand-in for SIL.LCModel.Core.KernelInterfaces.ITsString."""

    def __init__(self, text):
        self.Text = text


class _FakeMultiString:
    """Stand-in for IMultiString: a WS-handle-keyed store."""

    def __init__(self, values):
        self._values = values

    def get_String(self, handle):
        return _FakeTsString(self._values.get(handle, ""))


class _FakeGuid:
    """Stand-in for System.Guid -- str() is all GetSyncableProperties uses."""

    def __init__(self, text):
        self._text = text

    def __str__(self):
        return self._text


class _FakeRA:
    """Stand-in for an IFsClosedFeature / IFsSymFeatVal reference (or, for
    the segment test, a phoneme -- both only need a .Guid here)."""

    def __init__(self, guid_text):
        self.Guid = _FakeGuid(guid_text)


class _FakeClosedValue:
    """Stand-in for IFsClosedValue (already the right shape post-'cast')."""

    def __init__(self, feature_guid, value_guid):
        self.FeatureRA = _FakeRA(feature_guid)
        self.ValueRA = _FakeRA(value_guid)


class _FakeFeatStruc:
    """Stand-in for the owned IFsFeatStruc."""

    def __init__(self, guid_text, specs):
        self.Guid = _FakeGuid(guid_text)
        self.FeatureSpecsOC = specs


class _FakeBaseNaturalClass:
    """
    Reproduces the LIVE pythonnet behaviour confirmed against Ngoreme FLEx
    (2026-08-19): an object returned by GetAll() is wrapped under the BASE
    IPhNaturalClass interface. .ClassName, .Name, .Abbreviation,
    .Description are visible (declared on the base interface / its
    ancestors), but .FeaturesOA (declared on the concrete IPhNCFeatures)
    and .SegmentsRC (declared on the concrete IPhNCSegments) are
    deliberately NOT set here, exactly matching
    hasattr(nc, "FeaturesOA") is False / hasattr(nc, "SegmentsRC") is
    False measured live even for populated real objects.

    The hidden data is reachable only via the _hidden_* attributes, which
    the fake cast helpers below expose -- mirroring how a real
    IPhNCFeatures(nc) / IPhNCSegments(nc) pythonnet cast reveals the
    concrete interface's members.
    """

    def __init__(self, class_name, name_text, hidden_feat_struc=None,
                 hidden_segments=None):
        self.ClassName = class_name
        self.Name = _FakeMultiString({1: name_text})
        self.Abbreviation = _FakeMultiString({})
        self.Description = _FakeMultiString({})
        self._hidden_feat_struc = hidden_feat_struc
        self._hidden_segments = (
            hidden_segments if hidden_segments is not None else []
        )
        # Deliberately no self.FeaturesOA / self.SegmentsRC assignment.


class _FakeFeaturesCastView:
    """Stand-in for the concrete IPhNCFeatures interface view."""

    def __init__(self, base):
        self.FeaturesOA = base._hidden_feat_struc
        self.Name = base.Name
        self.ClassName = base.ClassName


class _FakeSegmentsCastView:
    """Stand-in for the concrete IPhNCSegments interface view."""

    def __init__(self, base):
        self.SegmentsRC = base._hidden_segments
        self.Name = base.Name
        self.ClassName = base.ClassName


class _FakeWS:
    def __init__(self, ws_id, handle):
        self.Id = ws_id
        self.Handle = handle


class _FakeWritingSystemOperations:
    def GetAll(self):
        return [_FakeWS("en", 1)]


class _FakeProject:
    def __init__(self):
        self.WritingSystems = _FakeWritingSystemOperations()


class TestNaturalClassSyncPythonnetBaseInterfaceView:
    """
    BEHAVIOURAL regression coverage (not just source-text pattern locks)
    for the 2026-08-19 live-verification failure. These exercise the real
    GetSyncableProperties/ApplySyncableProperties code against a fake
    object that reproduces pythonnet's base-IPhNaturalClass view -- the
    exact shape GetAll() actually returns -- with IPhNCFeatures /
    IPhNCSegments / ITsString / IFsClosedValue monkeypatched to simple
    Python stand-ins so no SIL.LCModel/live project is required.

    These tests are provably red against the hasattr-gated code this
    module replaced: that code required hasattr(nc, "FeaturesOA") /
    hasattr(nc, "SegmentsRC") to be True to enter its capture branch, and
    _FakeBaseNaturalClass deliberately never sets either attribute
    (reproducing what pythonnet actually does for GetAll()'s results), so
    the old gate always skipped the branch and never emitted
    Features/FeaturesGuid/PhonemeGuids -- exactly the silent data-loss
    this whole fix closes.
    """

    @pytest.fixture(autouse=True)
    def _patch_lcm_names(self, monkeypatch):
        import flexicon.code.Grammar.NaturalClassOperations as nco

        monkeypatch.setattr(nco, "ITsString", lambda x: x)
        monkeypatch.setattr(
            nco, "IPhNCFeatures", lambda obj: _FakeFeaturesCastView(obj)
        )
        monkeypatch.setattr(
            nco, "IPhNCSegments", lambda obj: _FakeSegmentsCastView(obj)
        )
        monkeypatch.setattr(nco, "IFsClosedValue", lambda x: x)

    def test_getsyncable_properties_emits_features_for_base_typed_object(self):
        from flexicon.code.Grammar.NaturalClassOperations import (
            NaturalClassOperations,
        )

        feat_guid = "6e11afce-5b3a-4463-8c56-040699b9d77a"
        val_guid = "a8ab1fa1-2c7b-4e19-98a5-096e1154f6dd"
        struct_guid = "f7b73472-9dd2-4133-81bd-a6fed8be5e84"

        fake_struct = _FakeFeatStruc(
            struct_guid, [_FakeClosedValue(feat_guid, val_guid)]
        )
        fake_nc = _FakeBaseNaturalClass(
            "PhNCFeatures", "Nasals", hidden_feat_struc=fake_struct
        )

        # Sanity check: this fake genuinely reproduces the live symptom.
        assert not hasattr(fake_nc, "FeaturesOA"), (
            "Fixture bug: the fake must NOT expose FeaturesOA directly, "
            "matching pythonnet's base-interface view."
        )

        ops = NaturalClassOperations(_FakeProject())
        props = ops.GetSyncableProperties(fake_nc)

        assert props.get("FeaturesGuid") == struct_guid
        assert props.get("Features") == [
            {"FeatureGuid": feat_guid, "ValueGuid": val_guid}
        ], (
            "GetSyncableProperties must emit Features/FeaturesGuid for a "
            "PhNCFeatures item even when FeaturesOA is not directly "
            "visible via hasattr/getattr -- it must discriminate via "
            "ClassName and cast, not gate on hasattr."
        )

    def test_getsyncable_properties_emits_phoneme_guids_for_base_typed_object(self):
        from flexicon.code.Grammar.NaturalClassOperations import (
            NaturalClassOperations,
        )

        phoneme_guid = "11111111-1111-1111-1111-111111111111"
        fake_phoneme = _FakeRA(phoneme_guid)  # only needs .Guid
        fake_nc = _FakeBaseNaturalClass(
            "PhNCSegments", "Stops", hidden_segments=[fake_phoneme]
        )

        assert not hasattr(fake_nc, "SegmentsRC"), (
            "Fixture bug: the fake must NOT expose SegmentsRC directly, "
            "matching pythonnet's base-interface view."
        )

        ops = NaturalClassOperations(_FakeProject())
        props = ops.GetSyncableProperties(fake_nc)

        assert props.get("PhonemeGuids") == [phoneme_guid], (
            "GetSyncableProperties must emit PhonemeGuids for a "
            "PhNCSegments item even when SegmentsRC is not directly "
            "visible via hasattr/getattr."
        )

    def test_getsyncable_properties_omits_features_for_segments_base_typed_object(self):
        """The two branches must not cross-contaminate: a PhNCSegments-
        classed fake must never emit Features/FeaturesGuid."""
        from flexicon.code.Grammar.NaturalClassOperations import (
            NaturalClassOperations,
        )

        fake_nc = _FakeBaseNaturalClass("PhNCSegments", "Stops")
        ops = NaturalClassOperations(_FakeProject())
        props = ops.GetSyncableProperties(fake_nc)

        assert "Features" not in props
        assert "FeaturesGuid" not in props


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
