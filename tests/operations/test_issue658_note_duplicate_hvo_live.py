#
#   test_issue658_note_duplicate_hvo_live.py
#
#   Live verification for issue #658 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_658_"


class TestIssue658NoteDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("NoteOperations", "write")
    def test_duplicate_reply_insert_after_raw_object_view(self, target_sandbox):
        project = target_sandbox
        entry = project.LexEntry.Create(f"{TEST_PREFIX}entry")
        try:
            parent = project.Notes.Create(entry, f"{TEST_PREFIX}parent")
            reply_a = project.Notes.AddReply(parent, f"{TEST_PREFIX}a")
            reply_b = project.Notes.AddReply(parent, f"{TEST_PREFIX}b")
            reply_c = project.Notes.AddReply(parent, f"{TEST_PREFIX}c")

            raw_mid = project.Object(reply_b.Hvo)
            dup = project.Notes.Duplicate(raw_mid, insert_after=True, deep=False)

            order = [r.Hvo for r in project.Notes.GetReplies(parent)]
            assert order.index(dup.Hvo) == order.index(reply_b.Hvo) + 1

            project.Notes.Delete(dup)
            project.Notes.Delete(reply_c)
            project.Notes.Delete(reply_b)
            project.Notes.Delete(reply_a)
            project.Notes.Delete(parent)
        finally:
            project.LexEntry.Delete(entry)
