#
#   test_issue776_baseops_sort_hvo_live.py
#
#   Live verification for issue #776 BaseOperations Sort HVO lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_776_"


class TestIssue776BaseOpsSortHvoLive:
    """Sort must reorder when the parent is resolved via Object(hvo)."""

    @pytest.mark.live_phase("LexSenseOperations", "modify")
    def test_sort_orders_senses_for_object_hvo_parent(self, target_sandbox):
        entry = target_sandbox.LexiconEntries.Create(f"{TEST_PREFIX}lemma")
        target_sandbox.Senses.Create(entry, gloss=f"{TEST_PREFIX}zzz")
        target_sandbox.Senses.Create(entry, gloss=f"{TEST_PREFIX}aaa")
        target_sandbox.Senses.Create(entry, gloss=f"{TEST_PREFIX}mmm")
        assert entry.SensesOS.Count == 3

        entry_raw = target_sandbox.Object(entry.Hvo)
        ws = target_sandbox.GetDefaultAnalysisWSHandle()
        from SIL.LCModel import ITsString

        sorted_count = target_sandbox.Senses.Sort(
            entry_raw,
            key_func=lambda s: ITsString(s.Gloss.get_String(ws)).Text or "",
        )
        assert sorted_count == 3

        glosses = [
            ITsString(entry.SensesOS[i].Gloss.get_String(ws)).Text
            for i in range(entry.SensesOS.Count)
        ]
        assert glosses == [
            f"{TEST_PREFIX}aaa",
            f"{TEST_PREFIX}mmm",
            f"{TEST_PREFIX}zzz",
        ]
