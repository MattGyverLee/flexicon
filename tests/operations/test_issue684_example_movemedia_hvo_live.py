#
#   test_issue684_example_movemedia_hvo_live.py
#
#   Live verification for issue #684 Example MoveMediaFile HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_684_"


def test_issue684_move_media_file_after_hvo_refetch(target_sandbox):
    """MoveMediaFile succeeds when caller holds Object(hvo) view of ICmFile."""
    entry = target_sandbox.LexEntry.Create(f"{TEST_PREFIX}entry")
    sense = target_sandbox.Senses.Create(entry, f"{TEST_PREFIX}gloss")
    try:
        ex_src = target_sandbox.Examples.Create(sense, f"{TEST_PREFIX}src")
        ex_dst = target_sandbox.Examples.Create(sense, f"{TEST_PREFIX}dst")
        media = target_sandbox.Media.Create(f"{TEST_PREFIX}probe.wav")
        ex_src.MediaFilesOS.Add(media)
        bare_media = target_sandbox.Object(media.Hvo)

        moved = target_sandbox.Examples.MoveMediaFile(bare_media, ex_src, ex_dst)
        assert moved is True

        src_hvos = {m.Hvo for m in target_sandbox.Examples.GetMediaFiles(ex_src)}
        dst_hvos = {m.Hvo for m in target_sandbox.Examples.GetMediaFiles(ex_dst)}
        assert media.Hvo not in src_hvos
        assert media.Hvo in dst_hvos

        target_sandbox.Examples.Delete(ex_dst)
        target_sandbox.Examples.Delete(ex_src)
    finally:
        target_sandbox.LexEntry.Delete(entry)
