#
#   test_issue552_example_duplicate_hvo_live.py
#
#   Live verification for issue #552 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_552_"


class TestIssue552ExampleDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("ExampleOperations", "write")
    def test_duplicate_insert_after_raw_object_view(self, target_sandbox):
        entry = target_sandbox.LexiconAllEntries().__next__()
        sense = target_sandbox.Senses.Create(entry, f"{TEST_PREFIX}gloss")
        e0 = target_sandbox.Examples.Create(sense, f"{TEST_PREFIX}first")
        e1 = target_sandbox.Examples.Create(sense, f"{TEST_PREFIX}second")
        e2 = target_sandbox.Examples.Create(sense, f"{TEST_PREFIX}third")

        raw_mid = target_sandbox.Object(e1.Hvo)
        dup = target_sandbox.Examples.Duplicate(raw_mid, insert_after=True, deep=False)

        order = [ex.Hvo for ex in target_sandbox.Examples.GetAll(sense)]
        assert order.index(dup.Hvo) == order.index(e1.Hvo) + 1

        target_sandbox.Examples.Delete(dup)
        target_sandbox.Examples.Delete(e2)
        target_sandbox.Examples.Delete(e1)
        target_sandbox.Examples.Delete(e0)
        target_sandbox.Senses.Delete(sense)
