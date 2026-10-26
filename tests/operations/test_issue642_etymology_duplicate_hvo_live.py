#
#   test_issue642_etymology_duplicate_hvo_live.py
#
#   Live verification for issue #642 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_642_"


class TestIssue642EtymologyDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("EtymologyOperations", "write")
    def test_duplicate_insert_after_raw_object_view(self, target_sandbox):
        entry = target_sandbox.LexEntry.Create(f"{TEST_PREFIX}entry")
        try:
            form_a = f"{TEST_PREFIX}a"
            form_b = f"{TEST_PREFIX}b"
            form_c = f"{TEST_PREFIX}c"
            etym_a = target_sandbox.Etymology.Create(entry.Hvo, form=form_a)
            etym_b = target_sandbox.Etymology.Create(entry.Hvo, form=form_b)
            etym_c = target_sandbox.Etymology.Create(entry.Hvo, form=form_c)

            raw_mid = target_sandbox.Object(etym_b.Hvo)
            dup = target_sandbox.Etymology.Duplicate(
                raw_mid, insert_after=True, deep=False
            )

            order = [etym.Hvo for etym in entry.EtymologyOS]
            assert order.index(dup.Hvo) == order.index(etym_b.Hvo) + 1

            target_sandbox.Etymology.Delete(dup)
            target_sandbox.Etymology.Delete(etym_c)
            target_sandbox.Etymology.Delete(etym_b)
            target_sandbox.Etymology.Delete(etym_a)
        finally:
            target_sandbox.LexEntry.Delete(entry)
