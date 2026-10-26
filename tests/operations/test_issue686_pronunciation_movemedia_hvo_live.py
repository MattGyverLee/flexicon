#
#   test_issue686_pronunciation_movemedia_hvo_live.py
#
#   Live verification for issue #686 Pronunciation MoveMediaFile HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_686_"


def test_issue686_move_media_file_after_hvo_refetch(target_sandbox):
    """MoveMediaFile succeeds when caller holds Object(hvo) view of ICmFile."""
    entry = target_sandbox.LexEntry.Create(f"{TEST_PREFIX}entry")
    try:
        pron_src = target_sandbox.Pronunciations.Create(entry, f"{TEST_PREFIX}src")
        pron_dst = target_sandbox.Pronunciations.Create(entry, f"{TEST_PREFIX}dst")
        media = target_sandbox.Media.Create(f"{TEST_PREFIX}probe.wav")
        pron_src.MediaFilesOS.Add(media)
        bare_media = target_sandbox.Object(media.Hvo)

        moved = target_sandbox.Pronunciations.MoveMediaFile(bare_media, pron_src, pron_dst)
        assert moved is True

        src_hvos = {m.Hvo for m in target_sandbox.Pronunciations.GetMediaFiles(pron_src)}
        dst_hvos = {m.Hvo for m in target_sandbox.Pronunciations.GetMediaFiles(pron_dst)}
        assert media.Hvo not in src_hvos
        assert media.Hvo in dst_hvos

        target_sandbox.Pronunciations.Delete(pron_dst)
        target_sandbox.Pronunciations.Delete(pron_src)
    finally:
        target_sandbox.LexEntry.Delete(entry)
