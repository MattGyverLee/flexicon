#
#   test_issue640_getbeststring_live.py
#
#   Live verification for issue #640 GetBestString on real LCM multistrings.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project


class TestIssue640GetBestStringLive:
    """GetBestString must accept live multistring property values."""

    @pytest.mark.live_phase("WritingSystemOperations", "read")
    def test_get_best_string_on_lex_sense_gloss(self, sena3_sandbox):
        entries = list(sena3_sandbox.LexEntry.GetAll())
        if not entries:
            pytest.skip("Sena 3 has no lex entries")

        entry = entries[0]
        if entry.SensesOS.Count == 0:
            pytest.skip("First entry has no senses")

        gloss = entry.SensesOS[0].Gloss
        via_ws = sena3_sandbox.WritingSystems.GetBestString(gloss)
        via_project = sena3_sandbox.BestStr(gloss)
        direct = gloss.BestAnalysisVernacularAlternative.Text
        if direct == "***":
            direct = ""

        assert via_ws == direct
        assert via_project == direct
