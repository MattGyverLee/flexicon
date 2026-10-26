#
#   test_issue682_datanotebook_media_hvo_live.py
#
#   Live verification for issue #682 DataNotebook media HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_682_"


def test_issue682_remove_media_file_after_hvo_refetch(target_sandbox):
    """RemoveMediaFile detaches media when caller holds Object(hvo) view."""
    project = target_sandbox
    op = project.DataNotebook
    media_op = project.Media
    title = f"{TEST_PREFIX}media_hvo"
    record = op.Create(title)
    try:
        media = media_op.Create("dummy.wav")
        op.AddMediaFile(record, media)
        bare_media = project.Object(media.Hvo)
        op.RemoveMediaFile(record, bare_media)
        attached = list(op.GetMediaFiles(record))
        assert all(m.Hvo != media.Hvo for m in attached)
    finally:
        found = op.Find(title)
        if found is not None:
            op.Delete(found)
