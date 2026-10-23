#
#   test_issue692_lexsense_reorder_hvo_live.py
#
#   Live verification for issue #692 LexSense Reorder HVO membership partition.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_692_"


def _make_entry(sandbox, tag):
    return sandbox.LexEntry.Create(f"{TEST_PREFIX}{tag}")


class TestIssue692LexSenseReorderHvoLive:
    """Reorder must accept Object(hvo) views in sense_list without length errors."""

    @pytest.mark.live_phase("LexSenseOperations", "write")
    def test_reorder_partial_list_with_raw_object_views(self, target_sandbox):
        entry = _make_entry(target_sandbox, "entry")
        sense_ops = target_sandbox.Senses

        try:
            s0 = sense_ops.Create(entry, f"{TEST_PREFIX}a")
            s1 = sense_ops.Create(entry, f"{TEST_PREFIX}b")
            s2 = sense_ops.Create(entry, f"{TEST_PREFIX}c")

            raw_first = target_sandbox.Object(s0.Hvo)
            raw_second = target_sandbox.Object(s1.Hvo)
            sense_ops.Reorder(entry, [raw_second, raw_first])

            order = [s.Hvo for s in sense_ops.GetAll(entry)]
            assert order == [s1.Hvo, s0.Hvo, s2.Hvo]
        finally:
            target_sandbox.LexEntry.Delete(entry)
