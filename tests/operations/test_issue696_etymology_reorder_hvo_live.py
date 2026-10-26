#
#   test_issue696_etymology_reorder_hvo_live.py
#
#   Live verification for issue #696 Etymology Reorder HVO membership partition.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_696_"


def _make_entry_with_etymologies(sandbox, tag):
    entry = sandbox.LexEntry.Create(f"{TEST_PREFIX}{tag}")
    etym_ops = sandbox.Etymology
    e0 = etym_ops.Create(entry, source=f"{TEST_PREFIX}src0")
    e1 = etym_ops.Create(entry, source=f"{TEST_PREFIX}src1")
    return entry, e0, e1


class TestIssue696EtymologyReorderHvoLive:
    """Reorder must accept Object(hvo) views in etymology_list."""

    @pytest.mark.live_phase("EtymologyOperations", "write")
    def test_reorder_with_raw_object_views(self, target_sandbox):
        entry, e0, e1 = _make_entry_with_etymologies(target_sandbox, "entry")
        etym_ops = target_sandbox.Etymologies

        try:
            raw_first = target_sandbox.Object(e0.Hvo)
            raw_second = target_sandbox.Object(e1.Hvo)
            etym_ops.Reorder(entry, [raw_second, raw_first])

            order = [e.Hvo for e in etym_ops.GetAll(entry)]
            assert order == [e1.Hvo, e0.Hvo]
        finally:
            target_sandbox.LexEntry.Delete(entry)
