#
#   test_phoneme_feature_sync_issue253.py
#
#   Coverage for PhonemeOperations feature-structure sync -- spec
#   feature-structure-sync-gap, Task T9 (issue #253).
#
#   This file ships the BEHAVIOURALLY NEUTRAL half of T9 (Commit A of a
#   two-commit rollout): the C2 HVO-path cast (__GetPhonemeObject), the C6
#   key-presence gate in ApplySyncableProperties, and struct-GUID
#   threading -- all while on_unresolved still defaults to "skip". The
#   policy flip to "raise" (C7) and its contract tests land in the T9
#   follow-up commit (test_phoneme_feature_sync_issue253_flip.py), together
#   with the CHANGELOG BREAKING entry (spec D1).
#
#   Sections A/B/C are OFFLINE fake-object tests (no live LCM, no real
#   cast) -- copied from the proven pattern in test_issue252_pos_feature_sync.py.
#   Section D is LIVE (requires_live_project, target_sandbox) and exercises
#   the real apply path end-to-end with a valid spec; run with
#   `$env:FLEXLIBS_REQUIRE_LIVE = "1"` and -m requires_live_project.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest


# ============================================================================
# Section A -- shared offline fixtures (pattern from test_issue252_pos_feature_sync.py)
# ============================================================================


class _FakePhoneme:
    """Stand-in for an LCM phoneme object. ApplySyncableProperties only
    passes it through __GetPhonemeObject (no attribute is read before the
    feature gate), so an empty stand-in is sufficient with the seams below
    patched away."""


class _FakeWritingSystems:
    def GetAll(self):
        return []


class _FakeProject:
    """Minimal stand-in -- the offline tests monkeypatch the three feature-
    struct seams and the super() call, so PhonemeOperations never touches
    self.project beyond WritingSystems.GetAll() and the cast-recorder test's
    Object()."""

    writeEnabled = True
    WritingSystems = _FakeWritingSystems()

    def __init__(self):
        self._obj = _FakePhoneme()

    def Object(self, hvo):
        return self._obj


def _make_super_spy(records):
    def _spy(self, item, props, ws_map=None, fill_gaps=False):
        records.append(
            {
                "item": item,
                "props": dict(props),
                "ws_map": ws_map,
                "fill_gaps": fill_gaps,
            }
        )

    return _spy


def _make_apply_spy(records, raise_guid=None):
    def _spy(self, owner, prop_name, spec_dict, struct_guid=None,
             on_unresolved="raise", label=None):
        from flexicon.code.BaseOperations import FP_ParameterError

        records.append(
            {
                "owner": owner,
                "prop_name": prop_name,
                "spec_dict": spec_dict,
                "struct_guid": struct_guid,
                "on_unresolved": on_unresolved,
                "label": label,
            }
        )
        if raise_guid is not None:
            raise FP_ParameterError(
                f"ApplySyncableProperties: reference to GUID {raise_guid} "
                f"which does not exist in the target project."
            )
        return object()

    return _spy


def _make_cast_recorder():
    calls = []

    class _Recorder:
        def __init__(self, obj):
            calls.append(obj)

    return _Recorder, calls


@pytest.fixture
def phoneme_ops():
    from flexicon.code.Grammar.PhonemeOperations import PhonemeOperations

    return PhonemeOperations(_FakeProject())


# ============================================================================
# Section B -- ApplySyncableProperties presence gate (C6) + GUID threading
# ============================================================================


class TestApplyPresenceGate:
    """C6: the phoneme sync applies on key PRESENCE (or a present GUID
    sibling), never truthiness of the Features list alone. Every fixture
    here carries a FALSY-BUT-PRESENT value so presence and truthiness come
    apart immediately (T6b lesson applied from the start)."""

    def test_apply_base_props_pops_feature_keys_before_super(
        self, monkeypatch, phoneme_ops
    ):
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Grammar.PhonemeOperations import PhonemeOperations

        super_calls = []
        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy(super_calls)
        )
        apply_calls = []
        monkeypatch.setattr(
            PhonemeOperations, "_ApplyFeatureStruc", _make_apply_spy(apply_calls)
        )

        props = {
            "Features": [{"FeatureGuid": "F", "ValueGuid": "V"}],
            "FeaturesGuid": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "Name": "keep-me",
        }

        phoneme_ops.ApplySyncableProperties(_FakePhoneme(), props)

        assert len(super_calls) == 1
        received = super_calls[0]["props"]
        assert "Features" not in received
        assert "FeaturesGuid" not in received
        assert received == {"Name": "keep-me"}
        assert len(apply_calls) == 1

    def test_falsy_but_present_features_with_real_guid_still_triggers_apply(
        self, monkeypatch, phoneme_ops
    ):
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Grammar.PhonemeOperations import PhonemeOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        apply_calls = []
        monkeypatch.setattr(
            PhonemeOperations, "_ApplyFeatureStruc", _make_apply_spy(apply_calls)
        )

        guid = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        # Features is EMPTY (falsy) but the source emitted a non-empty
        # FeaturesGuid -> an empty-but-present feature struct. The old
        # `if features:` gate skipped this; the presence gate must not.
        props = {"Features": [], "FeaturesGuid": guid}

        phoneme_ops.ApplySyncableProperties(_FakePhoneme(), props)

        assert len(apply_calls) == 1, (
            "A present FeaturesGuid (with an empty Features list) must "
            "still trigger _ApplyFeatureStruc (C6 presence gate)."
        )
        assert apply_calls[0]["spec_dict"] == []
        assert apply_calls[0]["struct_guid"] == guid

    def test_guid_only_present_still_triggers_apply(self, monkeypatch, phoneme_ops):
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Grammar.PhonemeOperations import PhonemeOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        apply_calls = []
        monkeypatch.setattr(
            PhonemeOperations, "_ApplyFeatureStruc", _make_apply_spy(apply_calls)
        )

        guid = "12121212-1212-1212-1212-121212121212"
        # "Features" key intentionally ABSENT -- source with an empty
        # struct emits only FeaturesGuid.
        props = {"FeaturesGuid": guid}

        phoneme_ops.ApplySyncableProperties(_FakePhoneme(), props)

        assert len(apply_calls) == 1
        assert apply_calls[0]["spec_dict"] is None
        assert apply_calls[0]["struct_guid"] == guid

    def test_neither_key_present_never_calls_apply_feature_struc(
        self, monkeypatch, phoneme_ops
    ):
        from flexicon.code.BaseOperations import BaseOperations
        from flexicon.code.Grammar.PhonemeOperations import PhonemeOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        apply_calls = []
        monkeypatch.setattr(
            PhonemeOperations, "_ApplyFeatureStruc", _make_apply_spy(apply_calls)
        )

        phoneme_ops.ApplySyncableProperties(_FakePhoneme(), {})

        assert len(apply_calls) == 0

    def test_none_item_raises_fp_parameter_error(self, phoneme_ops):
        from flexicon.code.BaseOperations import FP_ParameterError

        with pytest.raises(FP_ParameterError):
            phoneme_ops.ApplySyncableProperties(None, {})


# ============================================================================
# Section C -- the C2 cast (IPhPhoneme) on the HVO path
# ============================================================================


class TestC2HvoPathCast:
    """C2: __GetPhonemeObject casts the bare project.Object(hvo) result to
    IPhPhoneme so a base-interface view cannot silently lose FeaturesOA.
    Mutation kill check: deleting the cast makes the first test FAIL."""

    def test_hvo_int_path_casts_to_iphphoneme(self, monkeypatch, phoneme_ops):
        import flexicon.code.Grammar.PhonemeOperations as phoneme_module

        recorder, calls = _make_cast_recorder()
        monkeypatch.setattr(phoneme_module, "IPhPhoneme", recorder)

        result = phoneme_ops._PhonemeOperations__GetPhonemeObject(123)

        assert len(calls) == 1, (
            "The int-HVO path must cast via IPhPhoneme(...) -- dropping the "
            "cast returns a bare object and this test FAILS."
        )
        assert isinstance(result, recorder)

    def test_object_path_passes_through_unchanged(self, monkeypatch, phoneme_ops):
        import flexicon.code.Grammar.PhonemeOperations as phoneme_module

        recorder, calls = _make_cast_recorder()
        monkeypatch.setattr(phoneme_module, "IPhPhoneme", recorder)

        obj = _FakePhoneme()
        result = phoneme_ops._PhonemeOperations__GetPhonemeObject(obj)

        assert calls == []
        assert result is obj


# ============================================================================
# Section D -- LIVE: real apply of a VALID spec on target_sandbox
# ============================================================================


@pytest.fixture
def phoneme_owner(target_sandbox):
    """A live TEST_-prefixed phoneme plus a real closed phonological feature
    and value minted via PhonFeatures -- everything _ApplyFeatureStruc needs
    to resolve a spec against a real feature system. Capture-and-restore in
    a finally: per the target_sandbox fixture contract."""
    sandbox = target_sandbox
    ph = sandbox.Phonemes.Create("TEST_253_p_feat")
    feat = sandbox.PhonFeatures.Create("TEST_253_feat", "t253f")
    value = sandbox.PhonFeatures.CreateValue(feat, "TEST_253_val", "t253v")

    yield sandbox, ph, feat, value

    try:
        sandbox.Phonemes.Delete(ph)
    except Exception:
        pass
    try:
        sandbox.PhonFeatures.Delete(feat)
    except Exception:
        pass


@pytest.mark.requires_live_project
class TestPhonemeFeatureSyncLive:
    """End-to-end apply through ApplySyncableProperties, re-reading the
    written state from a FRESH bare project.Object(ph.Hvo) fetch -- never
    from the reference held at write time."""

    @pytest.mark.live_phase("PhonemeOperations", "modify")
    def test_apply_valid_spec_preserves_struct_guid_and_specs(
        self, phoneme_owner
    ):
        from SIL.LCModel import IPhPhoneme, IFsClosedValue

        sandbox, ph, feat, value = phoneme_owner
        import uuid

        struct_guid = str(uuid.uuid4())
        phonemes = sandbox.Phonemes
        props = {
            "Features": [
                {"FeatureGuid": str(feat.Guid), "ValueGuid": str(value.Guid)}
            ],
            "FeaturesGuid": struct_guid,
        }

        phonemes.ApplySyncableProperties(ph, props)

        reread = IPhPhoneme(sandbox.Object(ph.Hvo))
        struct = reread.FeaturesOA
        assert struct is not None, "FeaturesOA must exist after apply"
        assert str(struct.Guid).lower() == struct_guid.lower(), (
            "struct_guid must be preserved on the newly-created structure."
        )
        specs = list(struct.FeatureSpecsOC)
        assert len(specs) == 1
        cv = IFsClosedValue(specs[0])
        assert str(cv.FeatureRA.Guid).lower() == str(feat.Guid).lower()
        assert str(cv.ValueRA.Guid).lower() == str(value.Guid).lower()