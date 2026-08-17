#
#   test_grammar_brackets_live.py
#
#   Live write-path verification for B2 batch 10/11 (Grammar): the 59
#   mutation sites bracketed in `with self._TransactionCM(...)` per
#   decision D5.
#
#   Structure copied from tests/operations/test_target_live_smoke.py,
#   the canonical template. Runs against the Target scratch project.
#
#   What this proves, per site class:
#
#     1. Round-trip -- the bracketed write reaches the LCM and survives a
#        re-query. Asserting on the value passed in would prove nothing,
#        so every assertion re-reads through the Operations getter.
#     2. Validation-outside-the-bracket -- a rejected input raises and
#        leaves the stored value untouched. This is the property D5's
#        per-site shape exists to preserve: a central dispatch-layer
#        bracket would have opened (and under B1 rolled back) an undo
#        task for each of these.
#     3. Delete round-trip -- the bracketed Remove really detaches the
#        object from its owning collection.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project


TEST_PREFIX = "TEST_"


class TestGrammarFixtureReachesLiveLCM:
    """Prove this module's writes land on a real LCM cache, not a mock."""

    @pytest.mark.live_phase("FLExProject", "read")
    def test_sandbox_opens_write_enabled(self, target_sandbox):
        assert target_sandbox.writeEnabled is True
        assert getattr(target_sandbox, "project", None) is not None, (
            "target_sandbox has no underlying LCM cache -- this is a "
            "mock, not a live project."
        )


class TestPOSBrackets:
    """POSOperations: Delete, SetName, SetAbbreviation, RemoveSubcategory."""

    @pytest.mark.live_phase("POSOperations", "modify")
    def test_setname_round_trips_through_lcm(self, target_sandbox):
        pos_ops = target_sandbox.POS
        created = pos_ops.Create(f"{TEST_PREFIX}pos_name", f"{TEST_PREFIX}pn")

        try:
            pos_ops.SetName(created, f"{TEST_PREFIX}renamed")
            # Re-query rather than trusting the argument we passed in.
            assert pos_ops.GetName(created) == f"{TEST_PREFIX}renamed"
        finally:
            pos_ops.Delete(created)

    @pytest.mark.live_phase("POSOperations", "modify")
    def test_setabbreviation_round_trips_through_lcm(self, target_sandbox):
        pos_ops = target_sandbox.POS
        created = pos_ops.Create(f"{TEST_PREFIX}pos_abbr", f"{TEST_PREFIX}pa")

        try:
            pos_ops.SetAbbreviation(created, f"{TEST_PREFIX}ab")
            assert pos_ops.GetAbbreviation(created) == f"{TEST_PREFIX}ab"
        finally:
            pos_ops.Delete(created)

    @pytest.mark.live_phase("POSOperations", "modify")
    def test_empty_name_rejected_with_value_unchanged(self, target_sandbox):
        """
        The empty-name guard sits OUTSIDE the bracket, so it raises without
        opening an undo task and without disturbing the stored value.
        """
        pos_ops = target_sandbox.POS
        created = pos_ops.Create(f"{TEST_PREFIX}pos_guard", f"{TEST_PREFIX}pg")

        try:
            before = pos_ops.GetName(created)

            with pytest.raises(FP_ParameterError):
                pos_ops.SetName(created, "   ")

            assert pos_ops.GetName(created) == before, (
                "A rejected SetName altered the stored name -- the "
                "validation guard is inside the transaction."
            )
        finally:
            pos_ops.Delete(created)

    @pytest.mark.live_phase("POSOperations", "delete")
    def test_delete_detaches_from_lcm(self, target_sandbox):
        pos_ops = target_sandbox.POS
        before = len(list(pos_ops.GetAll()))

        created = pos_ops.Create(f"{TEST_PREFIX}pos_delete", f"{TEST_PREFIX}pd")
        assert len(list(pos_ops.GetAll())) == before + 1

        pos_ops.Delete(created)
        assert len(list(pos_ops.GetAll())) == before, (
            "Delete did not remove the POS from the LCM collection."
        )


class TestPhonemeBrackets:
    """PhonemeOperations: Delete, SetRepresentation, SetDescription."""

    @pytest.mark.live_phase("PhonemeOperations", "modify")
    def test_setrepresentation_round_trips_through_lcm(self, target_sandbox):
        ops = target_sandbox.Phonemes
        created = ops.Create(f"{TEST_PREFIX}p")

        try:
            ops.SetRepresentation(created, f"{TEST_PREFIX}pp")
            assert ops.GetRepresentation(created) == f"{TEST_PREFIX}pp"
        finally:
            ops.Delete(created)

    @pytest.mark.live_phase("PhonemeOperations", "modify")
    def test_setdescription_round_trips_through_lcm(self, target_sandbox):
        ops = target_sandbox.Phonemes
        created = ops.Create(f"{TEST_PREFIX}p_desc")

        try:
            ops.SetDescription(created, "voiceless bilabial stop")
            assert ops.GetDescription(created) == "voiceless bilabial stop"
        finally:
            ops.Delete(created)

    @pytest.mark.live_phase("PhonemeOperations", "modify")
    def test_empty_representation_rejected_with_value_unchanged(
        self, target_sandbox
    ):
        ops = target_sandbox.Phonemes
        created = ops.Create(f"{TEST_PREFIX}p_guard")

        try:
            before = ops.GetRepresentation(created)

            with pytest.raises(FP_ParameterError):
                ops.SetRepresentation(created, "  ")

            assert ops.GetRepresentation(created) == before
        finally:
            ops.Delete(created)

    @pytest.mark.live_phase("PhonemeOperations", "delete")
    def test_delete_detaches_from_lcm(self, target_sandbox):
        ops = target_sandbox.Phonemes
        before = len(list(ops.GetAll()))

        created = ops.Create(f"{TEST_PREFIX}p_del")
        assert len(list(ops.GetAll())) == before + 1

        ops.Delete(created)
        assert len(list(ops.GetAll())) == before


class TestNaturalClassBrackets:
    """NaturalClassOperations: SetName, AddPhoneme, RemovePhoneme, Delete."""

    @pytest.mark.live_phase("NaturalClassOperations", "modify")
    def test_setname_round_trips_through_lcm(self, target_sandbox):
        ops = target_sandbox.NaturalClasses
        created = ops.Create(f"{TEST_PREFIX}nc", f"{TEST_PREFIX}NC")

        try:
            ops.SetName(created, f"{TEST_PREFIX}nc_renamed")
            assert ops.GetName(created) == f"{TEST_PREFIX}nc_renamed"
        finally:
            ops.Delete(created)

    @pytest.mark.live_phase("NaturalClassOperations", "modify")
    def test_add_and_remove_phoneme_round_trip(self, target_sandbox):
        """
        AddPhoneme and RemovePhoneme keep their membership guards outside
        the bracket; both mutations must still reach the LCM.
        """
        nc_ops = target_sandbox.NaturalClasses
        ph_ops = target_sandbox.Phonemes

        nc = nc_ops.Create(f"{TEST_PREFIX}nc_mem", f"{TEST_PREFIX}NCM")
        phoneme = ph_ops.Create(f"{TEST_PREFIX}p_mem")

        try:
            assert len(nc_ops.GetPhonemes(nc)) == 0

            nc_ops.AddPhoneme(nc, phoneme)
            assert len(nc_ops.GetPhonemes(nc)) == 1, (
                "AddPhoneme did not reach the LCM."
            )

            nc_ops.RemovePhoneme(nc, phoneme)
            assert len(nc_ops.GetPhonemes(nc)) == 0, (
                "RemovePhoneme did not reach the LCM."
            )
        finally:
            nc_ops.Delete(nc)
            ph_ops.Delete(phoneme)


class TestStratumAndEnvironmentBrackets:
    """StratumOperations.Delete and EnvironmentOperations Delete/SetName."""

    @pytest.mark.live_phase("StratumOperations", "delete")
    def test_stratum_delete_detaches_from_lcm(self, target_sandbox):
        ops = target_sandbox.Strata
        before = len(list(ops.GetAll()))

        created = ops.Create(f"{TEST_PREFIX}stratum")
        assert len(list(ops.GetAll())) == before + 1

        ops.Delete(created)
        assert len(list(ops.GetAll())) == before

    @pytest.mark.live_phase("EnvironmentOperations", "modify")
    def test_environment_setname_round_trips_through_lcm(self, target_sandbox):
        ops = target_sandbox.Environments
        created = ops.Create(f"{TEST_PREFIX}env")

        try:
            ops.SetName(created, f"{TEST_PREFIX}env_renamed")
            assert ops.GetName(created) == f"{TEST_PREFIX}env_renamed"
        finally:
            ops.Delete(created)

    @pytest.mark.live_phase("EnvironmentOperations", "delete")
    def test_environment_delete_detaches_from_lcm(self, target_sandbox):
        ops = target_sandbox.Environments
        before = len(list(ops.GetAll()))

        created = ops.Create(f"{TEST_PREFIX}env_del")
        assert len(list(ops.GetAll())) == before + 1

        ops.Delete(created)
        assert len(list(ops.GetAll())) == before


class TestPhonRuleBrackets:
    """PhonologicalRuleOperations: SetName, SetDescription, Delete."""

    @pytest.mark.live_phase("PhonologicalRuleOperations", "modify")
    def test_setname_and_setdescription_round_trip(self, target_sandbox):
        ops = target_sandbox.PhonRules
        created = ops.Create(f"{TEST_PREFIX}rule")

        try:
            ops.SetName(created, f"{TEST_PREFIX}rule_renamed")
            assert ops.GetName(created) == f"{TEST_PREFIX}rule_renamed"

            ops.SetDescription(created, "intervocalic voicing")
            assert ops.GetDescription(created) == "intervocalic voicing"
        finally:
            ops.Delete(created)

    @pytest.mark.live_phase("PhonologicalRuleOperations", "delete")
    def test_delete_detaches_from_lcm(self, target_sandbox):
        ops = target_sandbox.PhonRules
        before = len(list(ops.GetAll()))

        created = ops.Create(f"{TEST_PREFIX}rule_del")
        assert len(list(ops.GetAll())) == before + 1

        ops.Delete(created)
        assert len(list(ops.GetAll())) == before
