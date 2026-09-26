#
#   test_issue550_lexsense_duplicate_hvo_live.py
#
#   Live verification for issue #550 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_550_"


def _make_entry(sandbox, tag):
    return sandbox.LexEntry.Create(f"{TEST_PREFIX}{tag}")


class TestIssue550LexSenseDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("LexSenseOperations", "write")
    def test_duplicate_insert_after_raw_object_view(self, target_sandbox):
        entry = _make_entry(target_sandbox, "entry")
        sense_ops = target_sandbox.Senses

        try:
            s0 = sense_ops.Create(entry, f"{TEST_PREFIX}a")
            s1 = sense_ops.Create(entry, f"{TEST_PREFIX}b")
            s2 = sense_ops.Create(entry, f"{TEST_PREFIX}c")

            raw_mid = target_sandbox.Object(s1.Hvo)
            dup = sense_ops.Duplicate(raw_mid, insert_after=True, deep=False)

            order = [s.Hvo for s in sense_ops.GetAll(entry)]
            assert order.index(dup.Hvo) == order.index(s1.Hvo) + 1

            sense_ops.Delete(dup)
        finally:
            target_sandbox.LexEntry.Delete(entry)
