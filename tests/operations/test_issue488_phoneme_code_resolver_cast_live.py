#
#   test_issue488_phoneme_code_resolver_cast_live.py
#
#   Live gate for issue #488 PhonemeOperations code HVO resolver cast.
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_488_"


@pytest.mark.requires_live_project
class TestIssue488PhonemeCodeHvoGate:
    """
    RemoveCode resolves the code via __GetCodeObject and checks CodesOS
    membership -- requires a concrete IPhCode view on the HVO path.
    """

    @pytest.mark.live_phase("PhonemeOperations", "modify")
    def test_remove_code_via_genuine_code_hvo(self, target_sandbox):
        sandbox = target_sandbox
        ph_ops = sandbox.Phonemes

        phoneme = ph_ops.Create(f"{TEST_PREFIX}t")
        code = ph_ops.AddCode(phoneme, f"{TEST_PREFIX}[t]")
        hvo = phoneme.Hvo
        code_hvo = code.Hvo
        assert isinstance(hvo, int), (
            "test setup error: hvo must be a genuine Python int"
        )
        assert isinstance(code_hvo, int), (
            "test setup error: code hvo must be a genuine Python int"
        )

        try:
            assert len(ph_ops.GetCodes(hvo)) == 1
            ph_ops.RemoveCode(hvo, code_hvo)
            assert len(ph_ops.GetCodes(hvo)) == 0, (
                "RemoveCode via HVO pair did not reach CodesOS.Remove"
            )
        finally:
            ph_ops.Delete(phoneme)
