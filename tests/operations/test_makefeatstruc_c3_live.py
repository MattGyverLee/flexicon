#
#   test_makefeatstruc_c3_live.py
#
#   Shipped-suite live coverage for BaseOperations._MakeFeatStruc's C3
#   public surface (spec feature-structure-sync-gap, Task T14a).
#
#   T5 (commit 6643b483) generalized MakeFeatStruc into ONE implementation,
#   BaseOperations._MakeFeatStruc, backing both
#   InflectionFeatureOperations.MakeFeatStruc and
#   PhonFeatureOperations.MakeFeatStruc. Its new public surface -- a
#   RECURSIVE DICT spec shape and a `slot=` keyword -- was proven live by
#   the cycle-5 verification gate, but only via a disposable, uncommitted
#   probe file in a worktree that has since been removed. This file closes
#   that shipped-suite coverage gap. See
#   specs/feature-structure-sync-gap/evidence/live-cycle5-verification-t5.md
#   section 5 for the prose description this file was reconstructed from.
#
#   Uses target_sandbox (a fresh tempdir copy of the Target .fwbackup) for
#   every test -- never the shared, in-place Sena 3 project -- so a failed
#   assertion mid-test cannot leave residue in a project other agents share.
#   Every created object is prefixed TEST_.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon.code.BaseOperations import FP_ParameterError

pytestmark = pytest.mark.requires_live_project


TEST_PREFIX = "TEST_c14a_"


def _make_sense(sandbox, entry):
    """
    Return the entry's first sense, creating one via ILexSenseFactory if
    LexEntry.Create's default sense-creation somehow left it senseless.
    Mirrors the defensive pattern in test_feature_struc_resolver.py's
    feature_struc_family fixture.
    """
    from SIL.LCModel import ILexSenseFactory

    senses = list(entry.SensesOS)
    if senses:
        return senses[0]
    factory = sandbox.project.ServiceLocator.GetService(ILexSenseFactory)
    new_sense = factory.Create()
    entry.SensesOS.Add(new_sense)
    return new_sense


class TestMakeFeatStrucNestedDictLive:
    """
    C3 shape (a): a RECURSIVE DICT spec, resolved through
    InflectionFeatureOperations.MakeFeatStruc -> BaseOperations
    ._MakeFeatStruc, against a live MoStemMsa owner. Mirrors the cycle-5
    gate's own probe (evidence file section 5) exactly, including its use
    of HVO operands (plain name-string operands are NOT a supported
    _MakeFeatStruc operand -- see the gate's section 9 discrepancy note
    and _MakeFeatStruc's own docstring Notes).
    """

    @pytest.mark.live_phase("InflectionFeatureOperations", "add")
    def test_nested_dict_spec_round_trips_through_makefeatstruc(
        self, target_sandbox
    ):
        from SIL.LCModel import (
            IFsClosedValue,
            IFsComplexValue,
            IFsFeatStruc,
            IMoStemMsa,
        )

        sandbox = target_sandbox
        infl_ops = sandbox.InflectionFeatures

        entry = sandbox.LexEntry.Create(lexeme_form=f"{TEST_PREFIX}nested")
        try:
            sense = _make_sense(sandbox, entry)
            pos = sandbox.POS.Create(f"{TEST_PREFIX}nested_pos", "tnp")
            stem = sandbox.MSA.CreateStem(sense, pos)
            stem_hvo = stem.Hvo

            agreement_feat = infl_ops.Create(
                f"{TEST_PREFIX}agreement", "tca", type="complex"
            )
            number_feat = infl_ops.Create(
                f"{TEST_PREFIX}number", "tcn", type="closed"
            )
            sg_val = infl_ops.CreateValue(
                number_feat, f"{TEST_PREFIX}sg", "sg"
            )

            # Two-level RECURSIVE DICT spec, HVO operands throughout --
            # exactly the shape the (now-deleted) cycle-5 gate probe used.
            specs = {agreement_feat.Hvo: {number_feat.Hvo: sg_val.Hvo}}

            # Owner passed as a bare object -- MakeFeatStruc/
            # _ResolveFeatureStrucOwner discriminate on .ClassName and
            # cast internally; the caller never needs a pre-cast concrete
            # type.
            owner_obj = sandbox.Object(stem_hvo)
            infl_ops.MakeFeatStruc(specs, owner=owner_obj)

            # Anti-tautology: re-fetch via a FRESH IMoStemMsa cast of a
            # FRESH project.Object(hvo) lookup -- never the reference just
            # passed in or returned.
            fresh_stem = IMoStemMsa(sandbox.Object(stem_hvo))
            top_struct = fresh_stem.MsFeaturesOA
            assert top_struct is not None, (
                "MsFeaturesOA is None after MakeFeatStruc -- the struct "
                "was never attached to the owner."
            )

            top_specs = list(top_struct.FeatureSpecsOC)
            assert len(top_specs) == 1, (
                f"Expected exactly one top-level feature spec, found "
                f"{len(top_specs)}."
            )
            top_spec = IFsComplexValue(top_specs[0])
            assert (
                top_spec.FeatureRA.Name.BestAnalysisAlternative.Text
                == f"{TEST_PREFIX}agreement"
            ), "Top-level spec's FeatureRA does not name the agreement feature."

            nested_struct = IFsFeatStruc(top_spec.ValueOA)
            nested_specs = list(nested_struct.FeatureSpecsOC)
            assert len(nested_specs) == 1, (
                f"Expected exactly one nested feature spec, found "
                f"{len(nested_specs)}."
            )
            # FeatureSpecsOC entries are statically base-typed
            # (IFsFeatureSpecification) under pythonnet -- discriminate by
            # ClassName then cast explicitly, never hasattr-probe a
            # subtype member (spec D5).
            nested_spec = IFsClosedValue(nested_specs[0])
            assert (
                nested_spec.FeatureRA.Name.BestAnalysisAlternative.Text
                == f"{TEST_PREFIX}number"
            ), "Nested spec's FeatureRA does not name the number feature."
            assert (
                nested_spec.ValueRA.Name.BestAnalysisAlternative.Text
                == f"{TEST_PREFIX}sg"
            ), "Nested spec's ValueRA does not name the sg value."
        finally:
            sandbox.LexEntry.Delete(entry)


class TestMakeFeatStrucSlotDisambiguationLive:
    """
    C3's `slot=` keyword, exercised THROUGH MakeFeatStruc itself (not
    _ResolveFeatureStrucOwner directly -- that resolver-level coverage
    already exists in test_feature_struc_resolver.py and would not touch
    T5's new keyword on the public compose surface).
    """

    @pytest.mark.live_phase("InflectionFeatureOperations", "add")
    def test_slot_disambiguates_from_and_to_through_makefeatstruc(
        self, target_sandbox
    ):
        from SIL.LCModel import IFsClosedValue, IMoDerivAffMsa

        sandbox = target_sandbox
        infl_ops = sandbox.InflectionFeatures

        entry = sandbox.LexEntry.Create(lexeme_form=f"{TEST_PREFIX}slot")
        try:
            sense = _make_sense(sandbox, entry)
            pos_a = sandbox.POS.Create(f"{TEST_PREFIX}slot_posA", "tsa")
            pos_b = sandbox.POS.Create(f"{TEST_PREFIX}slot_posB", "tsb")
            deriv = sandbox.MSA.CreateDerivAff(sense, pos_a, pos_b)
            deriv_hvo = deriv.Hvo

            number_feat = infl_ops.Create(
                f"{TEST_PREFIX}slot_number", "tsn", type="closed"
            )
            sg_val = infl_ops.CreateValue(
                number_feat, f"{TEST_PREFIX}slot_sg", "sg"
            )
            pl_val = infl_ops.CreateValue(
                number_feat, f"{TEST_PREFIX}slot_pl", "pl"
            )

            # ONE MoDerivAffMsa, two independent owning properties
            # (FromMsFeaturesOA / ToMsFeaturesOA). Each call uses a FRESH
            # bare-object lookup -- never the same owner reference twice.
            owner_from = sandbox.Object(deriv_hvo)
            infl_ops.MakeFeatStruc(
                {number_feat.Hvo: sg_val.Hvo}, owner=owner_from, slot="From"
            )

            owner_to = sandbox.Object(deriv_hvo)
            infl_ops.MakeFeatStruc(
                {number_feat.Hvo: pl_val.Hvo}, owner=owner_to, slot="To"
            )

            # Anti-tautology: re-fetch via a FRESH IMoDerivAffMsa cast of a
            # FRESH project.Object(hvo) lookup.
            fresh_deriv = IMoDerivAffMsa(sandbox.Object(deriv_hvo))
            from_struct = fresh_deriv.FromMsFeaturesOA
            to_struct = fresh_deriv.ToMsFeaturesOA

            assert from_struct is not None and to_struct is not None, (
                "Both FromMsFeaturesOA and ToMsFeaturesOA must be attached "
                "-- one slot= call clobbered or skipped the other."
            )
            assert from_struct.Hvo != to_struct.Hvo, (
                "slot='From' and slot='To' attached to the SAME struct -- "
                "slot= disambiguation through MakeFeatStruc failed to "
                "route to two distinct owning properties."
            )

            from_specs = list(from_struct.FeatureSpecsOC)
            to_specs = list(to_struct.FeatureSpecsOC)
            assert len(from_specs) == 1 and len(to_specs) == 1

            from_cv = IFsClosedValue(from_specs[0])
            to_cv = IFsClosedValue(to_specs[0])
            assert (
                from_cv.ValueRA.Name.BestAnalysisAlternative.Text
                == f"{TEST_PREFIX}slot_sg"
            ), "From slot did not receive the sg value."
            assert (
                to_cv.ValueRA.Name.BestAnalysisAlternative.Text
                == f"{TEST_PREFIX}slot_pl"
            ), "To slot did not receive the pl value."
        finally:
            sandbox.LexEntry.Delete(entry)
            sandbox.POS.Delete(pos_a)
            sandbox.POS.Delete(pos_b)


class TestMakeFeatStrucAmbiguousOwnerNoSlotLive:
    """
    C1/C3 ruling, confirmed by reading _ResolveFeatureStrucOwner (and its
    FEATURE_STRUC_OWNER_TABLE) before writing this test: an owner whose
    ClassName has MORE THAN ONE feature-structure-owning property (e.g.
    MoDerivAffMsa: From/To) and NO slot= raises FP_ParameterError -- it is
    NEVER silently guessed. This is documented, deliberate behaviour, not
    a defect, so asserting the raise does not bless an unreviewed guess;
    it locks the one ruling the resolver actually enforces.
    """

    @pytest.mark.live_phase("InflectionFeatureOperations", "add")
    def test_ambiguous_owner_without_slot_raises_through_makefeatstruc(
        self, target_sandbox
    ):
        sandbox = target_sandbox
        infl_ops = sandbox.InflectionFeatures

        entry = sandbox.LexEntry.Create(lexeme_form=f"{TEST_PREFIX}ambig")
        try:
            sense = _make_sense(sandbox, entry)
            pos_a = sandbox.POS.Create(f"{TEST_PREFIX}ambig_posA", "taa")
            pos_b = sandbox.POS.Create(f"{TEST_PREFIX}ambig_posB", "tab")
            deriv = sandbox.MSA.CreateDerivAff(sense, pos_a, pos_b)
            deriv_hvo = deriv.Hvo

            owner_obj = sandbox.Object(deriv_hvo)
            with pytest.raises(FP_ParameterError) as excinfo:
                infl_ops.MakeFeatStruc({}, owner=owner_obj)
            assert "MoDerivAffMsa" in str(excinfo.value)
            assert "slot" in str(excinfo.value)

            # Confirm the raise happened BEFORE anything was attached --
            # a partial/guessed attach would be worse than the raise
            # itself.
            from SIL.LCModel import IMoDerivAffMsa

            fresh_deriv = IMoDerivAffMsa(sandbox.Object(deriv_hvo))
            assert fresh_deriv.FromMsFeaturesOA is None
            assert fresh_deriv.ToMsFeaturesOA is None
        finally:
            sandbox.LexEntry.Delete(entry)
            sandbox.POS.Delete(pos_a)
            sandbox.POS.Delete(pos_b)
