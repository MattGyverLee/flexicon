#
#   test_issue702_dedup_hvo_verify_live.py
#
#   Live verification for issue #702 merge dedup post-Remove HVO verification.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_702_"


def test_issue702_merge_dedup_does_not_false_count_removal(target_sandbox):
    """Merge auto-dedup removes duplicate examples without spurious FP_DeduplicationError."""
    entry = target_sandbox.LexEntry.Create(f"{TEST_PREFIX}entry")
    try:
        sense_a = target_sandbox.Senses.Create(entry, f"{TEST_PREFIX}a")
        sense_b = target_sandbox.Senses.Create(entry, f"{TEST_PREFIX}b")
        shared = f"{TEST_PREFIX}shared_example"
        target_sandbox.Examples.Create(sense_a, shared)
        target_sandbox.Examples.Create(sense_b, shared)

        target_sandbox.Senses.MergeObject(sense_a, sense_b, auto_deduplicate=True)

        examples = list(target_sandbox.Examples.GetAll(sense_a))
        assert len(examples) == 1
    finally:
        target_sandbox.LexEntry.Delete(entry)
