#
#   test_issue688_lexsense_movepicture_hvo_live.py
#
#   Live verification for issue #688 LexSense MovePicture HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_688_"

_MINIMAL_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d49444154789c62000100000500010d0a2db40000000049454e44ae"
    "426082"
)


def test_issue688_move_picture_after_hvo_refetch(target_sandbox, tmp_path):
    """MovePicture succeeds when caller holds Object(hvo) view of ICmPicture."""
    img = tmp_path / f"{TEST_PREFIX}probe.png"
    img.write_bytes(_MINIMAL_PNG)

    entry = target_sandbox.LexEntry.Create(f"{TEST_PREFIX}entry")
    try:
        sense_src = target_sandbox.Senses.Create(entry, f"{TEST_PREFIX}src")
        sense_dst = target_sandbox.Senses.Create(entry, f"{TEST_PREFIX}dst")
        picture = target_sandbox.Senses.AddPicture(sense_src, str(img), f"{TEST_PREFIX}cap")
        bare_picture = target_sandbox.Object(picture.Hvo)

        moved = target_sandbox.Senses.MovePicture(bare_picture, sense_src, sense_dst)
        assert moved is True

        src_hvos = {p.Hvo for p in target_sandbox.Senses.GetPictures(sense_src)}
        dst_hvos = {p.Hvo for p in target_sandbox.Senses.GetPictures(sense_dst)}
        assert picture.Hvo not in src_hvos
        assert picture.Hvo in dst_hvos
    finally:
        target_sandbox.LexEntry.Delete(entry)
