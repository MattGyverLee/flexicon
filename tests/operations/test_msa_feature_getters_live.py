#
#   test_msa_feature_getters_live.py
#
#   Live round-trip verification for issue #544: MSAOperations feature-
#   structure getters (GetStemFeatures / GetInflAffFeatures /
#   GetDerivFromFeatures / GetDerivToFeatures / GetFeatures).
#
#   Per the binding user constraint for this task, ALL live writes here go
#   through sena3_sandbox (a fresh tempdir copy of the Sena 3 .fwbackup) --
#   never target_sandbox / target_project. Modelled on
#   tests/operations/test_target_live_smoke.py and
#   tests/operations/test_makefeatstruc_c3_live.py, with the fixture
#   swapped and every created object TEST_544_-prefixed.
#
#   For each of the four owning properties (MsFeaturesOA / InflFeatsOA /
#   FromMsFeaturesOA / ToMsFeaturesOA): build a struct with MakeFeatStruc
#   (including one nested IFsComplexValue level), read it back with the
#   new getter, re-apply the getter's own output to a SECOND fresh MSA via
#   MakeFeatStruc, re-read that second MSA from the LCM, and assert the
#   two are equivalent -- proving the getter's output really is valid
#   MakeFeatStruc input (the round-trip the issue asks for).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_544_"


def _make_sense(sandbox, entry):
    """Return the entry's first sense, creating one if LexEntry.Create
    somehow left it senseless. Mirrors test_makefeatstruc_c3_live.py."""
    from SIL.LCModel import ILexSenseFactory

    senses = list(entry.SensesOS)
    if senses:
        return senses[0]
    factory = sandbox.project.ServiceLocator.GetService(ILexSenseFactory)
    new_sense = factory.Create()
    entry.SensesOS.Add(new_sense)
    return new_sense


class TestStemFeaturesRoundTripLive:
    @pytest.mark.live_phase("MSAOperations", "read")
    def test_get_stem_features_round_trips_through_make_feat_struc(
        self, sena3_sandbox
    ):
        from SIL.LCModel import IFsClosedValue, IFsComplexValue, IMoStemMsa

        project = sena3_sandbox
        assert project.writeEnabled is True
        infl_ops = project.InflectionFeatures

        entry1 = project.LexEntry.Create(f"{TEST_PREFIX}stem_src")
        entry2 = project.LexEntry.Create(f"{TEST_PREFIX}stem_dst")
        try:
            sense1 = _make_sense(project, entry1)
            sense2 = _make_sense(project, entry2)
            pos = project.POS.Create(f"{TEST_PREFIX}stem_pos", "T544sp")

            stem1 = project.MSA.CreateStem(sense1, pos)
            stem2 = project.MSA.CreateStem(sense2, pos)
            stem1_hvo = int(stem1.Hvo)
            stem2_hvo = int(stem2.Hvo)

            agreement_feat = infl_ops.Create(
                f"{TEST_PREFIX}stem_agr", "T544sa", type="complex"
            )
            number_feat = infl_ops.Create(
                f"{TEST_PREFIX}stem_num", "T544sn", type="closed"
            )
            sg_val = infl_ops.CreateValue(
                number_feat, f"{TEST_PREFIX}stem_sg", "sg"
            )

            specs = {agreement_feat.Hvo: {number_feat.Hvo: sg_val.Hvo}}
            infl_ops.MakeFeatStruc(specs, owner=project.Object(stem1_hvo))

            # PRE-state, read back from the LCM directly (not via the
            # getter under test).
            pre = IMoStemMsa(project.Object(stem1_hvo)).MsFeaturesOA
            assert pre is not None

            spec_out = project.MSA.GetStemFeatures(stem1_hvo)
            assert spec_out is not None
            agr_guid = str(agreement_feat.Guid)
            num_guid = str(number_feat.Guid)
            sg_guid = str(sg_val.Guid)
            assert spec_out == {agr_guid: {num_guid: sg_guid}}, (
                f"GetStemFeatures did not return the MakeFeatStruc-shaped "
                f"spec: {spec_out!r}"
            )

            # Round-trip: feed the getter's own output back into
            # MakeFeatStruc, targeting a SECOND, independent MSA.
            infl_ops.MakeFeatStruc(spec_out, owner=project.Object(stem2_hvo))

            # POST-state, re-queried from the LCM (never the reference
            # just passed in).
            fresh2 = IMoStemMsa(project.Object(stem2_hvo))
            post_struct = fresh2.MsFeaturesOA
            assert post_struct is not None, (
                "Round-trip MakeFeatStruc(getter_output, ...) did not "
                "attach a struct to the second MSA."
            )
            post_specs = list(post_struct.FeatureSpecsOC)
            assert len(post_specs) == 1
            complex_spec = IFsComplexValue(post_specs[0])
            assert str(complex_spec.FeatureRA.Guid) == agr_guid
            nested = list(complex_spec.ValueOA.FeatureSpecsOC)
            assert len(nested) == 1
            closed_spec = IFsClosedValue(nested[0])
            assert str(closed_spec.FeatureRA.Guid) == num_guid
            assert str(closed_spec.ValueRA.Guid) == sg_guid

            # The getter's output on the round-tripped MSA must match the
            # original (same shape, same GUIDs).
            spec_out2 = project.MSA.GetStemFeatures(stem2_hvo)
            assert spec_out2 == spec_out, (
                "Getter output diverged after a MakeFeatStruc round-trip: "
                f"{spec_out!r} != {spec_out2!r}"
            )
        finally:
            project.LexEntry.Delete(entry1)
            project.LexEntry.Delete(entry2)
            project.POS.Delete(pos)


class TestInflAffFeaturesRoundTripLive:
    @pytest.mark.live_phase("MSAOperations", "read")
    def test_get_infl_aff_features_round_trips_through_make_feat_struc(
        self, sena3_sandbox
    ):
        from SIL.LCModel import IFsClosedValue, IMoInflAffMsa

        project = sena3_sandbox
        infl_ops = project.InflectionFeatures

        entry1 = project.LexEntry.Create(
            f"{TEST_PREFIX}infl_src", morph_type_name="prefix"
        )
        entry2 = project.LexEntry.Create(
            f"{TEST_PREFIX}infl_dst", morph_type_name="prefix"
        )
        try:
            sense1 = _make_sense(project, entry1)
            sense2 = _make_sense(project, entry2)
            pos = project.POS.Create(f"{TEST_PREFIX}infl_pos", "T544ip")

            infl1 = project.MSA.CreateInflAff(sense1, pos)
            infl2 = project.MSA.CreateInflAff(sense2, pos)
            infl1_hvo = int(infl1.Hvo)
            infl2_hvo = int(infl2.Hvo)

            number_feat = infl_ops.Create(
                f"{TEST_PREFIX}infl_num", "T544in", type="closed"
            )
            pl_val = infl_ops.CreateValue(
                number_feat, f"{TEST_PREFIX}infl_pl", "pl"
            )

            specs = {number_feat.Hvo: pl_val.Hvo}
            infl_ops.MakeFeatStruc(specs, owner=project.Object(infl1_hvo))

            pre = IMoInflAffMsa(project.Object(infl1_hvo)).InflFeatsOA
            assert pre is not None

            spec_out = project.MSA.GetInflAffFeatures(infl1_hvo)
            num_guid = str(number_feat.Guid)
            pl_guid = str(pl_val.Guid)
            assert spec_out == {num_guid: pl_guid}

            infl_ops.MakeFeatStruc(spec_out, owner=project.Object(infl2_hvo))

            fresh2 = IMoInflAffMsa(project.Object(infl2_hvo))
            post_struct = fresh2.InflFeatsOA
            assert post_struct is not None
            post_specs = list(post_struct.FeatureSpecsOC)
            assert len(post_specs) == 1
            closed_spec = IFsClosedValue(post_specs[0])
            assert str(closed_spec.FeatureRA.Guid) == num_guid
            assert str(closed_spec.ValueRA.Guid) == pl_guid

            spec_out2 = project.MSA.GetInflAffFeatures(infl2_hvo)
            assert spec_out2 == spec_out

            # Also exercise the dispatching GetFeatures entry point.
            assert project.MSA.GetFeatures(infl1_hvo) == spec_out
        finally:
            project.LexEntry.Delete(entry1)
            project.LexEntry.Delete(entry2)
            project.POS.Delete(pos)


class TestDerivAffFeaturesRoundTripLive:
    @pytest.mark.live_phase("MSAOperations", "read")
    def test_get_deriv_from_and_to_features_round_trip_through_make_feat_struc(
        self, sena3_sandbox
    ):
        from SIL.LCModel import IFsClosedValue, IMoDerivAffMsa

        project = sena3_sandbox
        infl_ops = project.InflectionFeatures

        entry1 = project.LexEntry.Create(f"{TEST_PREFIX}deriv_src")
        entry2 = project.LexEntry.Create(f"{TEST_PREFIX}deriv_dst")
        try:
            sense1 = _make_sense(project, entry1)
            sense2 = _make_sense(project, entry2)
            pos_a = project.POS.Create(f"{TEST_PREFIX}deriv_posA", "T544da")
            pos_b = project.POS.Create(f"{TEST_PREFIX}deriv_posB", "T544db")

            deriv1 = project.MSA.CreateDerivAff(sense1, pos_a, pos_b)
            deriv2 = project.MSA.CreateDerivAff(sense2, pos_a, pos_b)
            deriv1_hvo = int(deriv1.Hvo)
            deriv2_hvo = int(deriv2.Hvo)

            number_feat = infl_ops.Create(
                f"{TEST_PREFIX}deriv_num", "T544dn", type="closed"
            )
            sg_val = infl_ops.CreateValue(
                number_feat, f"{TEST_PREFIX}deriv_sg", "sg"
            )
            pl_val = infl_ops.CreateValue(
                number_feat, f"{TEST_PREFIX}deriv_pl", "pl"
            )

            infl_ops.MakeFeatStruc(
                {number_feat.Hvo: sg_val.Hvo},
                owner=project.Object(deriv1_hvo),
                slot="From",
            )
            infl_ops.MakeFeatStruc(
                {number_feat.Hvo: pl_val.Hvo},
                owner=project.Object(deriv1_hvo),
                slot="To",
            )

            num_guid = str(number_feat.Guid)
            sg_guid = str(sg_val.Guid)
            pl_guid = str(pl_val.Guid)

            from_out = project.MSA.GetDerivFromFeatures(deriv1_hvo)
            to_out = project.MSA.GetDerivToFeatures(deriv1_hvo)
            assert from_out == {num_guid: sg_guid}
            assert to_out == {num_guid: pl_guid}

            # Dispatching entry point: slot required, never guessed.
            from flexicon.code.FLExProject import FP_ParameterError

            with pytest.raises(FP_ParameterError):
                project.MSA.GetFeatures(deriv1_hvo)
            assert project.MSA.GetFeatures(deriv1_hvo, slot="From") == from_out
            assert project.MSA.GetFeatures(deriv1_hvo, slot="To") == to_out

            # Round-trip both slots onto a SECOND, independent MSA.
            infl_ops.MakeFeatStruc(
                from_out, owner=project.Object(deriv2_hvo), slot="From"
            )
            infl_ops.MakeFeatStruc(
                to_out, owner=project.Object(deriv2_hvo), slot="To"
            )

            fresh2 = IMoDerivAffMsa(project.Object(deriv2_hvo))
            from_struct = fresh2.FromMsFeaturesOA
            to_struct = fresh2.ToMsFeaturesOA
            assert from_struct is not None and to_struct is not None
            assert from_struct.Hvo != to_struct.Hvo

            from_cv = IFsClosedValue(list(from_struct.FeatureSpecsOC)[0])
            to_cv = IFsClosedValue(list(to_struct.FeatureSpecsOC)[0])
            assert str(from_cv.FeatureRA.Guid) == num_guid
            assert str(from_cv.ValueRA.Guid) == sg_guid
            assert str(to_cv.FeatureRA.Guid) == num_guid
            assert str(to_cv.ValueRA.Guid) == pl_guid

            assert project.MSA.GetDerivFromFeatures(deriv2_hvo) == from_out
            assert project.MSA.GetDerivToFeatures(deriv2_hvo) == to_out
        finally:
            project.LexEntry.Delete(entry1)
            project.LexEntry.Delete(entry2)
            project.POS.Delete(pos_a)
            project.POS.Delete(pos_b)


class TestUnclassifiedAffixAndEmptyStructLive:
    @pytest.mark.live_phase("MSAOperations", "read")
    def test_unclassified_affix_msa_is_none_and_null_stem_is_none(
        self, sena3_sandbox
    ):
        project = sena3_sandbox

        entry = project.LexEntry.Create(f"{TEST_PREFIX}unclass")
        try:
            sense_unclass = _make_sense(project, entry)
            pos = project.POS.Create(f"{TEST_PREFIX}unclass_pos", "T544up")

            unclass_msa = project.MSA.CreateUnclassifiedAffix(sense_unclass, pos)
            assert project.MSA.GetFeatures(unclass_msa) is None
            assert project.MSA.GetFeatures(sense_unclass) is None

            entry2 = project.LexEntry.Create(f"{TEST_PREFIX}nullstem")
            try:
                sense2 = _make_sense(project, entry2)
                stem_msa = project.MSA.CreateStem(sense2, pos)
                # MsFeaturesOA never populated -- null owning property.
                assert project.MSA.GetStemFeatures(stem_msa) is None
                assert project.MSA.GetStemFeatures(sense2) is None
            finally:
                project.LexEntry.Delete(entry2)
        finally:
            project.LexEntry.Delete(entry)
            project.POS.Delete(pos)


class TestReadOnlyPassOverRealSena3Msas:
    """
    Read-only sweep over real Sena 3 MSAs -- no writes, so this could run
    against sena3_sandbox OR the in-place project; sena3_sandbox is used
    for consistency with the rest of this file and because it is already
    open for the write-path tests above in the same session.
    """

    @pytest.mark.live_phase("MSAOperations", "read")
    def test_get_features_does_not_raise_over_a_sample_of_real_msas(
        self, sena3_sandbox
    ):
        project = sena3_sandbox

        entries = list(project.LexEntry.GetAll())
        sample = entries[:25] if len(entries) > 25 else entries
        assert sample, "Sena 3 sandbox has no LexEntry data to sample."

        checked = 0
        for entry in sample:
            msas = project.MSA.GetAll(entry)
            for msa in msas:
                spec = project.MSA.GetFeatures(msa)
                assert spec is None or isinstance(spec, dict), (
                    f"GetFeatures returned an unexpected type "
                    f"{type(spec).__name__} for a real MSA (hvo="
                    f"{getattr(msa, 'Hvo', '?')})."
                )
                checked += 1

        assert checked > 0, (
            "Sampled Sena 3 entries owned no MSAs at all -- widen the "
            "sample or pick different entries."
        )
