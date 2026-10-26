#
#   test_issue694_example_reorder_hvo_live.py
#
#   Live verification for issue #694 Example Reorder HVO membership partition.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_694_"


def _make_entry_with_examples(sandbox, tag):
    entry = sandbox.LexEntry.Create(f"{TEST_PREFIX}{tag}")
    sense = sandbox.Senses.Create(entry, f"{TEST_PREFIX}sense")
    ex_ops = sandbox.Examples
    e0 = ex_ops.Create(sense, f"{TEST_PREFIX}ex0")
    e1 = ex_ops.Create(sense, f"{TEST_PREFIX}ex1")
    return entry, sense, e0, e1


class TestIssue694ExampleReorderHvoLive:
    """Reorder must accept Object(hvo) views in example_list."""

    @pytest.mark.live_phase("ExampleOperations", "write")
    def test_reorder_with_raw_object_views(self, target_sandbox):
        entry, sense, e0, e1 = _make_entry_with_examples(target_sandbox, "entry")
        ex_ops = target_sandbox.Examples

        try:
            raw_first = target_sandbox.Object(e0.Hvo)
            raw_second = target_sandbox.Object(e1.Hvo)
            ex_ops.Reorder(sense, [raw_second, raw_first])

            order = [ex.Hvo for ex in ex_ops.GetAll(sense)]
            assert order == [e1.Hvo, e0.Hvo]
        finally:
            target_sandbox.LexEntry.Delete(entry)
