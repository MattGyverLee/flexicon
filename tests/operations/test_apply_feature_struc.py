#
#   test_apply_feature_struc.py
#
#   Live coverage for BaseOperations._ApplyFeatureStruc /
#   _ApplyFeatureStrucSpecMap -- spec feature-structure-sync-gap, Task T4.
#
#   T4 extracts the shared recursive-apply algorithm that used to be
#   duplicated verbatim as NaturalClassOperations.__ApplyFeatures and
#   PhonemeOperations.__ApplyFeatures. Those two classes' own live tests
#   (test_natural_classes.py, test_phonemes.py) already cover the LEGACY
#   flat-list wire shape end-to-end through their public
#   GetSyncableProperties/ApplySyncableProperties surface -- this file
#   covers _ApplyFeatureStruc DIRECTLY (as the generic helper any C1 owner
#   can use), including the C4 recursive-dict wire shape (C4a) that no
#   NC/Phoneme call site drives yet.
#
#   All assertions re-read from a FRESH project.Object(hvo)/direct
#   attribute fetch after the write, never from the reference held at
#   write time (asserting on the value passed in proves nothing).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import sys

import pytest


def _require_lcmodel():
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")


@pytest.fixture
def msa_owner(target_sandbox):
    """
    A live MoStemMsa (owns MsFeaturesOA) plus the InflectionFeatures
    operations instance used to mint real feature/value/complex-feature/
    type definitions -- everything _ApplyFeatureStruc needs to resolve a
    spec against something real.
    """
    _require_lcmodel()
    from SIL.LCModel import ILexSenseFactory

    sandbox = target_sandbox
    entry = sandbox.LexEntry.Create(lexeme_form="TEST_applyfs")
    senses = list(entry.SensesOS)
    if not senses:
        factory = sandbox.project.ServiceLocator.GetService(ILexSenseFactory)
        new_sense = factory.Create()
        entry.SensesOS.Add(new_sense)
        senses = [new_sense]
    pos_obj = sandbox.POS.Create("TEST_applyfs_pos", "tap")
    stem = sandbox.MSA.CreateStem(senses[0], pos_obj)

    yield sandbox, stem, entry, pos_obj

    try:
        sandbox.LexEntry.Delete(entry)
    except Exception:
        pass
    try:
        sandbox.POS.Delete(pos_obj)
    except Exception:
        pass


@pytest.mark.requires_live_project
class TestApplyFeatureStrucLegacyListLive:
    """Legacy flat-list wire shape (C4a back-compat input), driven
    directly through _ApplyFeatureStruc rather than through NC/Phoneme's
    own ApplySyncableProperties (which already has its own live coverage)."""

    @pytest.mark.live_phase("BaseOperations", "modify")
    def test_apply_legacy_list_creates_struct_preserves_guid_and_spec(
        self, msa_owner
    ):
        import uuid

        sandbox, stem, entry, pos_obj = msa_owner
        infl_ops = sandbox.InflectionFeatures

        feat = infl_ops.Create("TEST_applyfs_feat", "tafe", type="closed")
        value = infl_ops.CreateValue(feat, "TEST_applyfs_val", "tava")
        struct_guid = str(uuid.uuid4())

        concrete_owner, prop_name = sandbox.MSA._ResolveFeatureStrucOwner(stem)
        assert prop_name == "MsFeaturesOA"

        result = sandbox.MSA._ApplyFeatureStruc(
            concrete_owner,
            prop_name,
            [{"FeatureGuid": str(feat.Guid), "ValueGuid": str(value.Guid)}],
            struct_guid=struct_guid,
            on_unresolved="raise",
            label="TEST stem",
        )
        assert result is not None

        # Re-read from a FRESH bare-object fetch, not the reference above.
        reread_bare = sandbox.Object(stem.Hvo)
        reread_owner, reread_prop = sandbox.MSA._ResolveFeatureStrucOwner(
            reread_bare
        )
        reread_struct = getattr(reread_owner, reread_prop)
        assert reread_struct is not None
        assert str(reread_struct.Guid).lower() == struct_guid.lower(), (
            "struct_guid must be preserved on the newly-created structure."
        )

        c4 = sandbox.MSA._GetFeatureStruc(reread_struct)
        assert c4["specs"] == {str(feat.Guid): str(value.Guid)}

    @pytest.mark.live_phase("BaseOperations", "modify")
    def test_apply_legacy_list_twice_is_idempotent(self, msa_owner):
        sandbox, stem, entry, pos_obj = msa_owner
        infl_ops = sandbox.InflectionFeatures

        feat = infl_ops.Create("TEST_applyfs_idem_feat", "taif", type="closed")
        value = infl_ops.CreateValue(feat, "TEST_applyfs_idem_val", "taiv")

        concrete_owner, prop_name = sandbox.MSA._ResolveFeatureStrucOwner(stem)
        specs = [{"FeatureGuid": str(feat.Guid), "ValueGuid": str(value.Guid)}]

        sandbox.MSA._ApplyFeatureStruc(
            concrete_owner, prop_name, specs, on_unresolved="raise",
            label="TEST stem",
        )
        sandbox.MSA._ApplyFeatureStruc(
            concrete_owner, prop_name, specs, on_unresolved="raise",
            label="TEST stem",
        )

        reread_bare = sandbox.Object(stem.Hvo)
        reread_owner, reread_prop = sandbox.MSA._ResolveFeatureStrucOwner(
            reread_bare
        )
        reread_struct = getattr(reread_owner, reread_prop)
        assert reread_struct.FeatureSpecsOC.Count == 1, (
            "Re-applying the same spec twice must not duplicate it "
            "(idempotency, C5)."
        )

    @pytest.mark.live_phase("BaseOperations", "modify")
    def test_apply_raise_mode_raises_on_unresolved_feature_guid(self, msa_owner):
        from flexicon.code.BaseOperations import FP_ParameterError

        sandbox, stem, entry, pos_obj = msa_owner
        bogus_guid = "00000000-0000-0000-0000-000000000001"

        concrete_owner, prop_name = sandbox.MSA._ResolveFeatureStrucOwner(stem)

        with pytest.raises(FP_ParameterError, match=bogus_guid):
            sandbox.MSA._ApplyFeatureStruc(
                concrete_owner,
                prop_name,
                [{"FeatureGuid": bogus_guid,
                  "ValueGuid": "00000000-0000-0000-0000-000000000002"}],
                on_unresolved="raise",
                label="TEST stem 'unresolved'",
            )

    @pytest.mark.live_phase("BaseOperations", "modify")
    def test_apply_skip_mode_silently_skips_unresolved_guid(self, msa_owner):
        sandbox, stem, entry, pos_obj = msa_owner
        bogus_guid = "00000000-0000-0000-0000-000000000003"

        concrete_owner, prop_name = sandbox.MSA._ResolveFeatureStrucOwner(stem)

        # Must not raise.
        sandbox.MSA._ApplyFeatureStruc(
            concrete_owner,
            prop_name,
            [{"FeatureGuid": bogus_guid,
              "ValueGuid": "00000000-0000-0000-0000-000000000004"}],
            on_unresolved="skip",
            label="TEST stem 'skip'",
        )

        reread_bare = sandbox.Object(stem.Hvo)
        reread_owner, reread_prop = sandbox.MSA._ResolveFeatureStrucOwner(
            reread_bare
        )
        reread_struct = getattr(reread_owner, reread_prop)
        # A struct is still created (ownership-first always creates the
        # shell), but the unresolved spec itself must not be inserted.
        assert reread_struct is None or reread_struct.FeatureSpecsOC.Count == 0


@pytest.mark.requires_live_project
class TestApplyFeatureStrucC4DictLive:
    """
    C4 recursive-dict wire shape (C4a) -- not yet driven by any NC/Phoneme
    call site (capture stays legacy until T9b), so this is the only live
    coverage of this branch until then.
    """

    @pytest.mark.live_phase("BaseOperations", "modify")
    def test_apply_flat_c4_dict_creates_closed_value(self, msa_owner):
        sandbox, stem, entry, pos_obj = msa_owner
        infl_ops = sandbox.InflectionFeatures

        feat = infl_ops.Create("TEST_applyfs_c4_feat", "tacf", type="closed")
        value = infl_ops.CreateValue(feat, "TEST_applyfs_c4_val", "tacv")

        concrete_owner, prop_name = sandbox.MSA._ResolveFeatureStrucOwner(stem)
        spec_dict = {
            "TypeGuid": None,
            "specs": {str(feat.Guid): str(value.Guid)},
        }

        sandbox.MSA._ApplyFeatureStruc(
            concrete_owner, prop_name, spec_dict, on_unresolved="raise",
            label="TEST stem C4",
        )

        reread_bare = sandbox.Object(stem.Hvo)
        reread_owner, reread_prop = sandbox.MSA._ResolveFeatureStrucOwner(
            reread_bare
        )
        reread_struct = getattr(reread_owner, reread_prop)
        c4 = sandbox.MSA._GetFeatureStruc(reread_struct)
        assert c4["specs"] == {str(feat.Guid): str(value.Guid)}

    @pytest.mark.live_phase("BaseOperations", "modify")
    def test_apply_nested_c4_dict_creates_complex_value_and_recurses(
        self, msa_owner
    ):
        sandbox, stem, entry, pos_obj = msa_owner
        infl_ops = sandbox.InflectionFeatures

        closed_feat = infl_ops.Create(
            "TEST_applyfs_nest_feat", "tanf", type="closed"
        )
        feat_value = infl_ops.CreateValue(
            closed_feat, "TEST_applyfs_nest_val", "tanv"
        )
        complex_feat = infl_ops.Create(
            "TEST_applyfs_nest_complex", "tanc", type="complex"
        )
        inner_type = infl_ops.TypeCreate("TEST_applyfs_nest_type", "tanty")

        concrete_owner, prop_name = sandbox.MSA._ResolveFeatureStrucOwner(stem)
        spec_dict = {
            "TypeGuid": None,
            "specs": {
                str(complex_feat.Guid): {
                    "TypeGuid": str(inner_type.Guid),
                    "specs": {str(closed_feat.Guid): str(feat_value.Guid)},
                },
            },
        }

        sandbox.MSA._ApplyFeatureStruc(
            concrete_owner, prop_name, spec_dict, on_unresolved="raise",
            label="TEST stem nested C4",
        )

        reread_bare = sandbox.Object(stem.Hvo)
        reread_owner, reread_prop = sandbox.MSA._ResolveFeatureStrucOwner(
            reread_bare
        )
        reread_struct = getattr(reread_owner, reread_prop)
        c4 = sandbox.MSA._GetFeatureStruc(reread_struct)

        assert c4["TypeGuid"] is None
        assert set(c4["specs"].keys()) == {str(complex_feat.Guid)}
        nested = c4["specs"][str(complex_feat.Guid)]
        assert nested["TypeGuid"] == str(inner_type.Guid), (
            "Per-level TypeGuid must be applied on the nested struct."
        )
        assert nested["specs"] == {str(closed_feat.Guid): str(feat_value.Guid)}

    @pytest.mark.live_phase("BaseOperations", "modify")
    def test_apply_c4_dict_raises_on_unresolved_type_guid(self, msa_owner):
        from flexicon.code.BaseOperations import FP_ParameterError

        sandbox, stem, entry, pos_obj = msa_owner
        bogus_type_guid = "00000000-0000-0000-0000-000000000005"

        concrete_owner, prop_name = sandbox.MSA._ResolveFeatureStrucOwner(stem)
        spec_dict = {"TypeGuid": bogus_type_guid, "specs": {}}

        with pytest.raises(FP_ParameterError, match=bogus_type_guid):
            sandbox.MSA._ApplyFeatureStruc(
                concrete_owner, prop_name, spec_dict, on_unresolved="raise",
                label="TEST stem bogus type",
            )
