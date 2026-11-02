#
#   test_issue776_baseops_sort_hvo_live.py
#
#   Live verification for issue #776: BaseOperations.Sort and
#   _ApplySequenceOrder compare members by HVO, not proxy identity.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_776_"


def _three_senses(sandbox):
    entry = sandbox.LexEntry.Create(f"{TEST_PREFIX}lemma")
    s_c = sandbox.Senses.Create(entry, gloss=f"{TEST_PREFIX}c")
    s_a = sandbox.Senses.Create(entry, gloss=f"{TEST_PREFIX}a")
    s_b = sandbox.Senses.Create(entry, gloss=f"{TEST_PREFIX}b")
    # LexEntry.Create may add a default sense; clear it from the picture by
    # deleting any sense that is not one of ours so the order is exactly 3.
    ours = {s_c.Hvo, s_a.Hvo, s_b.Hvo}
    for extra in [s for s in entry.SensesOS if s.Hvo not in ours]:
        sandbox.Senses.Delete(extra)
    return entry, s_c, s_a, s_b


class TestIssue776BaseOpsSortHvoLive:
    @pytest.mark.live_phase("LexSenseOperations", "modify")
    def test_sort_with_raw_views_reorders_by_hvo(self, target_sandbox):
        entry, s_c, s_a, s_b = _three_senses(target_sandbox)
        before = [s.Hvo for s in entry.SensesOS]
        assert before == [s_c.Hvo, s_a.Hvo, s_b.Hvo]
        rank = {s_a.Hvo: 0, s_b.Hvo: 1, s_c.Hvo: 2}

        # key_func receives members; a raw Object(hvo) view is what callers
        # hold, so the sort key hands back those views.
        count = target_sandbox.Senses.Sort(
            entry, key_func=lambda s: rank[target_sandbox.Object(s.Hvo).Hvo]
        )
        assert count == 3
        after = [s.Hvo for s in entry.SensesOS]
        assert after == [s_a.Hvo, s_b.Hvo, s_c.Hvo]

    @pytest.mark.live_phase("LexSenseOperations", "modify")
    def test_apply_sequence_order_accepts_raw_object_views(self, target_sandbox):
        entry, s_c, s_a, s_b = _three_senses(target_sandbox)
        raw = [target_sandbox.Object(h) for h in (s_b.Hvo, s_a.Hvo, s_c.Hvo)]
        with target_sandbox.Senses._TransactionCM("test 776"):
            target_sandbox.Senses._ApplySequenceOrder(entry.SensesOS, raw)
        after = [s.Hvo for s in entry.SensesOS]
        assert after == [s_b.Hvo, s_a.Hvo, s_c.Hvo]
