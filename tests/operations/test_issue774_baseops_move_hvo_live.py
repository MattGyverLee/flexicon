#
#   test_issue774_baseops_move_hvo_live.py
#
#   Live verification for issue #774 BaseOperations MoveDown HVO lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_774_"


class TestIssue774BaseOpsMoveHvoLive:
    """MoveDown must find the item when passed as raw Object(hvo)."""

    @pytest.mark.live_phase("LexSenseOperations", "modify")
    def test_move_down_finds_raw_sense_in_senses_os(self, target_sandbox):
        entry = target_sandbox.LexiconEntries.Create(f"{TEST_PREFIX}lemma")
        sense_a = target_sandbox.Senses.Create(entry, gloss=f"{TEST_PREFIX}a")
        sense_b = target_sandbox.Senses.Create(entry, gloss=f"{TEST_PREFIX}b")
        assert entry.SensesOS.Count >= 2

        sense_b_hvo = sense_b.Hvo
        sense_b_raw = target_sandbox.Object(sense_b_hvo)
        order_before = [s.Hvo for s in entry.SensesOS]

        moved = target_sandbox.Senses.MoveDown(entry, sense_b_raw, positions=1)
        assert moved == 1, "MoveDown should succeed for Object(hvo) argument"
        order_after = [s.Hvo for s in entry.SensesOS]
        assert order_after.index(sense_b_hvo) == order_before.index(sense_b_hvo) + 1
