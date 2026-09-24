#
#   test_issue323_note_replies_live.py
#
#   Live coverage for issue #323: reply attach and GetReplies round-trip.
#
#   Copyright 2026
#

import pytest


TEST_PREFIX = "TEST_323_"


@pytest.mark.requires_live_project
def test_add_reply_and_get_replies_roundtrip(target_sandbox):
    project = target_sandbox
    entry = project.LexEntry.Create(f"{TEST_PREFIX}entry")
    parent = project.Notes.Create(entry, f"{TEST_PREFIX}parent")
    reply = project.Notes.AddReply(parent, f"{TEST_PREFIX}reply")
    try:
        replies = list(project.Notes.GetReplies(parent))
        assert any(r.Hvo == reply.Hvo for r in replies), (
            "AddReply must attach a reply discoverable by GetReplies"
        )
    finally:
        project.Notes.Delete(reply)
        project.Notes.Delete(parent)
        project.LexEntry.Delete(entry)
