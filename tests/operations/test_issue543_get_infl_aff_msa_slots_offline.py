#
#   test_issue543_get_infl_aff_msa_slots_offline.py
#
#   Source ratchets for issue #543: GetInflAffMsaSlots on MSAOperations.
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
_LIVE_GATE = (
    pathlib.Path(__file__).resolve().parent
    / "test_issue543_get_infl_aff_msa_slots_live.py"
)


def _get_infl_aff_msa_slots_source():
    text = _MSA_OPS.read_text(encoding="utf-8")
    match = re.search(
        r"(def GetInflAffMsaSlots\(self.*?)(?=\n    @OperationsMethod|\n    def |\Z)",
        text,
        re.DOTALL,
    )
    assert match, "GetInflAffMsaSlots not found in MSAOperations.py"
    return match.group(0)


class TestIssue543GetInflAffMsaSlotsOffline:
    def test_get_infl_aff_msa_slots_exists(self):
        assert "def GetInflAffMsaSlots(" in _MSA_OPS.read_text(encoding="utf-8")

    def test_reads_slots_rc_without_write_guard(self):
        src = _get_infl_aff_msa_slots_source()
        assert "SlotsRC" in src
        assert "_EnsureWriteEnabled" not in src
        assert "_TransactionCM" not in src
        assert "return list(slots_rc)" in src or "return []" in src

    def test_non_infl_returns_empty_via_helper(self):
        text = _MSA_OPS.read_text(encoding="utf-8")
        assert "def __TryResolveInflAffMsa(" in text
        getter = _get_infl_aff_msa_slots_source()
        assert "__TryResolveInflAffMsa" in getter

    def test_issue543_live_gate_module_exists(self):
        assert _LIVE_GATE.is_file(), "missing live gate module for #543"
        body = _LIVE_GATE.read_text(encoding="utf-8")
        assert "requires_live_project" in body
        assert "GetInflAffMsaSlots" in body
