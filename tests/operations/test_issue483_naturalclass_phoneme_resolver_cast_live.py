#
#   test_issue483_naturalclass_phoneme_resolver_cast_live.py
#
#   Live gate for issue #483 NaturalClassOperations phoneme HVO resolver cast.
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_483_"


@pytest.mark.requires_live_project
class TestIssue483NaturalClassPhonemeHvoGate:
    """
    AddPhoneme resolves the phoneme via __GetPhonemeObject and mutates
    SegmentsRC -- requires a concrete IPhPhoneme view.
    """

    @pytest.mark.live_phase("NaturalClassOperations", "modify")
    def test_add_phoneme_via_genuine_phoneme_hvo(self, target_sandbox):
        sandbox = target_sandbox
        nc_ops = sandbox.NaturalClasses
        ph_ops = sandbox.Phonemes

        nc = nc_ops.Create(f"{TEST_PREFIX}nc", f"{TEST_PREFIX}NC")
        phoneme = ph_ops.Create(f"{TEST_PREFIX}p")
        hvo = nc.Hvo
        phoneme_hvo = phoneme.Hvo
        assert isinstance(hvo, int), (
            "test setup error: hvo must be a genuine Python int"
        )
        assert isinstance(phoneme_hvo, int), (
            "test setup error: phoneme hvo must be a genuine Python int"
        )
        nc_hvo = hvo

        try:
            assert len(nc_ops.GetPhonemes(nc_hvo)) == 0
            nc_ops.AddPhoneme(nc_hvo, phoneme_hvo)
            assert len(nc_ops.GetPhonemes(nc_hvo)) == 1, (
                "AddPhoneme via HVO pair did not reach SegmentsRC"
            )
            nc_ops.RemovePhoneme(nc_hvo, phoneme_hvo)
            assert len(nc_ops.GetPhonemes(nc_hvo)) == 0
        finally:
            nc_ops.Delete(nc)
            ph_ops.Delete(phoneme)
