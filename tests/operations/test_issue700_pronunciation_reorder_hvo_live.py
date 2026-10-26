#
#   test_issue700_pronunciation_reorder_hvo_live.py
#
#   Live verification for issue #700 Pronunciation Reorder HVO membership partition.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_700_"


def _make_entry_with_pronunciations(sandbox, tag):
    entry = sandbox.LexEntry.Create(f"{TEST_PREFIX}{tag}")
    pron_ops = sandbox.Pronunciations
    p0 = pron_ops.Create(entry, f"{TEST_PREFIX}p0")
    p1 = pron_ops.Create(entry, f"{TEST_PREFIX}p1")
    return entry, p0, p1


class TestIssue700PronunciationReorderHvoLive:
    """Reorder must accept Object(hvo) views in pronunciation_list."""

    @pytest.mark.live_phase("PronunciationOperations", "write")
    def test_reorder_with_raw_object_views(self, target_sandbox):
        entry, p0, p1 = _make_entry_with_pronunciations(target_sandbox, "entry")
        pron_ops = target_sandbox.Pronunciations

        try:
            raw_first = target_sandbox.Object(p0.Hvo)
            raw_second = target_sandbox.Object(p1.Hvo)
            pron_ops.Reorder(entry, [raw_second, raw_first])

            order = [p.Hvo for p in pron_ops.GetAll(entry)]
            assert order == [p1.Hvo, p0.Hvo]
        finally:
            target_sandbox.LexEntry.Delete(entry)
