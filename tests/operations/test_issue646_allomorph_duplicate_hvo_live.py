#
#   test_issue646_allomorph_duplicate_hvo_live.py
#
#   Live verification for issue #646 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_646_"


class TestIssue646AllomorphDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("AllomorphOperations", "write")
    def test_duplicate_insert_after_raw_object_view(self, target_sandbox):
        entry = target_sandbox.LexEntry.Create(f"{TEST_PREFIX}entry")
        try:
            target_sandbox.Allomorphs.Create(entry, f"{TEST_PREFIX}lex")
            allo_b = target_sandbox.Allomorphs.Create(
                entry, f"{TEST_PREFIX}b", morphType="suffix"
            )
            allo_c = target_sandbox.Allomorphs.Create(
                entry, f"{TEST_PREFIX}c", morphType="suffix"
            )

            raw_mid = target_sandbox.Object(allo_b.Hvo)
            dup = target_sandbox.Allomorphs.Duplicate(
                raw_mid, insert_after=True, deep=False
            )

            order = [a.Hvo for a in entry.AlternateFormsOS]
            assert order.index(dup.Hvo) == order.index(allo_b.Hvo) + 1

            target_sandbox.Allomorphs.Delete(dup)
            target_sandbox.Allomorphs.Delete(allo_c)
            target_sandbox.Allomorphs.Delete(allo_b)
        finally:
            target_sandbox.LexEntry.Delete(entry)
