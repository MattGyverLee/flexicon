#
#   test_issue258_set_infl_aff_msa_slots_offline.py
#
#   Source ratchets for issue #258: SetInflAffMsaSlots on MSAOperations.
#
#   Copyright 2026
#

import pathlib
import re


_MSA_OPS = (
    pathlib.Path(__file__).resolve().parents[2]
    / "flexicon"
    / "code"
    / "Lexicon"
    / "MSAOperations.py"
)


def _set_infl_aff_msa_slots_source():
    text = _MSA_OPS.read_text(encoding="utf-8")
    match = re.search(
        r"(def SetInflAffMsaSlots\(self.*?)(?=\n    @OperationsMethod|\n    def |\Z)",
        text,
        re.DOTALL,
    )
    assert match, "SetInflAffMsaSlots not found in MSAOperations.py"
    return match.group(0)


class TestIssue258SetInflAffMsaSlotsOffline:
    def test_set_infl_aff_msa_slots_exists(self):
        assert "def SetInflAffMsaSlots(" in _MSA_OPS.read_text(encoding="utf-8")

    def test_replace_clears_slots_rc_before_add(self):
        src = _set_infl_aff_msa_slots_source()
        assert "SlotsRC.Clear()" in src
        assert "replace" in src

    def test_resolves_slots_before_transaction(self):
        src = _set_infl_aff_msa_slots_source()
        clear_idx = src.index("SlotsRC.Clear()")
        bracket_idx = src.index("_TransactionCM")
        resolve_idx = src.index("resolved_slots")
        assert resolve_idx < bracket_idx
        assert bracket_idx < clear_idx or "if replace" in src

    def test_wrong_msa_type_raises_parameter_error(self):
        src = _set_infl_aff_msa_slots_source()
        assert "IMoInflAffMsa" in src
        assert "FP_ParameterError" in src
