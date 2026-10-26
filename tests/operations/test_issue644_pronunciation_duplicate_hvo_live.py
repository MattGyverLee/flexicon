#
#   test_issue644_pronunciation_duplicate_hvo_live.py
#
#   Live verification for issue #644 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_644_"


class TestIssue644PronunciationDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("PronunciationOperations", "write")
    def test_duplicate_insert_after_raw_object_view(self, target_sandbox):
        entry = target_sandbox.LexEntry.Create(f"{TEST_PREFIX}entry")
        try:
            form_a = f"{TEST_PREFIX}a"
            form_b = f"{TEST_PREFIX}b"
            form_c = f"{TEST_PREFIX}c"
            pron_a = target_sandbox.Pronunciations.Create(entry, form_a)
            pron_b = target_sandbox.Pronunciations.Create(entry, form_b)
            pron_c = target_sandbox.Pronunciations.Create(entry, form_c)

            raw_mid = target_sandbox.Object(pron_b.Hvo)
            dup = target_sandbox.Pronunciations.Duplicate(
                raw_mid, insert_after=True, deep=False
            )

            order = [pron.Hvo for pron in entry.PronunciationsOS]
            assert order.index(dup.Hvo) == order.index(pron_b.Hvo) + 1

            target_sandbox.Pronunciations.Delete(dup)
            target_sandbox.Pronunciations.Delete(pron_c)
            target_sandbox.Pronunciations.Delete(pron_b)
            target_sandbox.Pronunciations.Delete(pron_a)
        finally:
            target_sandbox.LexEntry.Delete(entry)
