#
#   test_issue690_lexsense_removepicture_hvo_live.py
#
#   Live verification for issue #690 LexSense RemovePicture HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_690_"

_MINIMAL_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d49444154789c62000100000500010d0a2db40000000049454e44ae"
    "426082"
)


def test_issue690_remove_picture_after_hvo_refetch(target_sandbox, tmp_path):
    """RemovePicture succeeds when caller holds Object(hvo) view of ICmPicture."""
    img = tmp_path / f"{TEST_PREFIX}probe.png"
    img.write_bytes(_MINIMAL_PNG)

    entry = target_sandbox.LexEntry.Create(f"{TEST_PREFIX}entry")
    try:
        sense = target_sandbox.Senses.Create(entry, f"{TEST_PREFIX}sense")
        picture = target_sandbox.Senses.AddPicture(sense, str(img), f"{TEST_PREFIX}cap")
        bare_picture = target_sandbox.Object(picture.Hvo)

        target_sandbox.Senses.RemovePicture(sense, bare_picture)

        remaining = {p.Hvo for p in target_sandbox.Senses.GetPictures(sense)}
        assert picture.Hvo not in remaining
    finally:
        target_sandbox.LexEntry.Delete(entry)
