#
#   test_issue746_phoneme_removecode_hvo_live.py
#
#   Live verification for issue #746 Phoneme CodesOS HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_746_"


@pytest.mark.requires_live_project
class TestIssue746PhonemeRemoveCodeHvoLive:
    """RemoveCode must not rely on Python proxy identity in CodesOS."""

    @pytest.mark.live_phase("PhonemeOperations", "modify")
    def test_remove_code_via_bare_object_view(self, target_sandbox):
        ph_ops = target_sandbox.Phonemes

        phoneme = ph_ops.Create(f"{TEST_PREFIX}t")
        try:
            code = ph_ops.AddCode(phoneme, f"{TEST_PREFIX}allophone")
            assert len(ph_ops.GetCodes(phoneme)) == 1

            bare_code = target_sandbox.Object(code.Hvo)
            ph_ops.RemoveCode(phoneme, bare_code)
            assert len(ph_ops.GetCodes(phoneme)) == 0
        finally:
            ph_ops.Delete(phoneme)

    @pytest.mark.live_phase("PhonemeOperations", "modify")
    def test_remove_code_via_hvo_int(self, target_sandbox):
        ph_ops = target_sandbox.Phonemes

        phoneme = ph_ops.Create(f"{TEST_PREFIX}p")
        try:
            code = ph_ops.AddCode(phoneme, f"{TEST_PREFIX}code")
            code_hvo = int(code.Hvo)
            assert len(ph_ops.GetCodes(phoneme)) == 1

            ph_ops.RemoveCode(phoneme, code_hvo)
            assert len(ph_ops.GetCodes(phoneme)) == 0
        finally:
            ph_ops.Delete(phoneme)
