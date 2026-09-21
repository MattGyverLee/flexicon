#
#   test_phoneme_feature_sync_issue253_flip.py
#
#   Coverage for the C7 policy flip in PhonemeOperations feature-structure
#   sync -- spec feature-structure-sync-gap, Task T9 (closes issue #253).
#
#   Commit B of a two-commit rollout: this file ships with the commit that
#   flips PhonemeOperations.__ApplyFeatures from a silent
#   `on_unresolved="skip"` default to an explicit `on_unresolved="raise"`,
#   matching NaturalClassOperations (C7): a feature/value GUID that does not
#   resolve in the target project is a data-fidelity loss and must RAISE,
#   not be silently dropped. The behaviorally-neutral half of T9 (C2 cast,
#   C6 presence gate, struct-GUID threading) landed in the preceding commit
#   with test_phoneme_feature_sync_issue253.py; this file pins only the
#   flip contract the CHANGELOG BREAKING entry announces (spec D1).
#
#   Sections A/B are OFFLINE fake-object tests (no live LCM, no real cast)
#   -- copied from the proven pattern in test_issue252_pos_feature_sync.py.
#   Section C is LIVE (requires_live_project, target_sandbox) and exercises
#   the REAL on_unresolved="raise" path end-to-end; run with
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
    """Stand-in for an LCM phoneme object -- same contract as the parent
    issue253 test file: nothing is read off the object before the feature
    gate, so an empty stand-in suffices with the seams patched away."""


class _FakeWritingSystems:
    def GetAll(self):
        return []


class _FakeProject:
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


@pytest.fixture
def phoneme_ops():
    from flexicon.code.Grammar.PhonemeOperations import PhonemeOperations

    return PhonemeOperations(_FakeProject())


# ============================================================================
# Section B -- the flipped default threads "raise" (C7)
# ============================================================================


class TestApplyRaiseContract:
    """C7: the flip is real -- PhonemeOperations.__ApplyFeatures defaults
    to on_unresolved="raise", and an unresolvable GUID surfaces as a loud
    FP_ParameterError through the public ApplySyncableProperties surface,
    never a silent drop. (Raising itself is _ApplyFeatureStruc's job; its
    real behaviour is covered live in Section C. Here the contract is
    pinned through the public surface with the seam spy raising.)"""

    def test_raise_default_threads_through_apply_syncable_properties(
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

        props = {"Features": [{"FeatureGuid": "F", "ValueGuid": "V"}]}

        phoneme_ops.ApplySyncableProperties(_FakePhoneme(), props)

        assert len(apply_calls) == 1
        assert apply_calls[0]["on_unresolved"] == "raise", (
            "PhonemeOperations must pass on_unresolved='raise' by default "
            "(C7, close #253) -- not the pre-T9 'skip'."
        )

    def test_unresolvable_guid_raises_through_public_surface(
        self, monkeypatch, phoneme_ops
    ):
        from flexicon.code.BaseOperations import (
            FP_ParameterError,
            BaseOperations,
        )
        from flexicon.code.Grammar.PhonemeOperations import PhonemeOperations

        monkeypatch.setattr(
            BaseOperations, "ApplySyncableProperties", _make_super_spy([])
        )
        apply_calls = []
        monkeypatch.setattr(
            PhonemeOperations,
            "_ApplyFeatureStruc",
            _make_apply_spy(apply_calls, raise_guid="bogus-guid"),
        )

        props = {
            "Features": [
                {"FeatureGuid": "bogus-guid", "ValueGuid": "any-value"}
            ]
        }

        with pytest.raises(FP_ParameterError):
            phoneme_ops.ApplySyncableProperties(_FakePhoneme(), props)

        assert len(apply_calls) == 1, (
            "The unresolvable spec must reach _ApplyFeatureStruc (so the "
            "raise is the resolver's real verdict, not an early bail)."
        )


# ============================================================================
# Section C -- LIVE: the real on_unresolved="raise" path on target_sandbox
# ============================================================================


@pytest.fixture
def phoneme_owner(target_sandbox):
    """A live TEST_-prefixed phoneme plus a real closed phonological feature
    and value minted via PhonFeatures. Capture-and-restore in a finally:
    per the target_sandbox fixture contract."""
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
class TestPhonemeFeatureSyncLiveFlip:
    """The flip's end-to-end consequence: an unresolvable feature GUID
    RAISES FP_ParameterError through the real write path and leaves no
    partial spec behind."""

    @pytest.mark.live_phase("PhonemeOperations", "modify")
    def test_unresolvable_feature_guid_raises_and_writes_nothing(
        self, phoneme_owner
    ):
        from flexicon.code.exceptions import FP_ParameterError
        from SIL.LCModel import IPhPhoneme

        sandbox, ph, feat, value = phoneme_owner
        phonemes = sandbox.Phonemes
        bogus = "00000000-0000-0000-0000-000000000000"
        props = {
            "Features": [{"FeatureGuid": bogus, "ValueGuid": str(value.Guid)}]
        }

        with pytest.raises(FP_ParameterError):
            phonemes.ApplySyncableProperties(ph, props)

        reread = IPhPhoneme(sandbox.Object(ph.Hvo))
        struct = reread.FeaturesOA
        if struct is not None:
            assert len(list(struct.FeatureSpecsOC)) == 0, (
                "A raising apply must not leave a silent partial spec behind."
            )