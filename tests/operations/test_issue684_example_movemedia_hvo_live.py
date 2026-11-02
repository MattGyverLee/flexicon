#
#   test_issue684_example_movemedia_hvo_live.py
#
#   Live check, superseded by issue #831: Example.MoveMediaFile is withdrawn.
#   With an HVO-refetched ICmFile handle (the #684 scenario) it must raise
#   FP_ParameterError and must not move or delete anything.
#
#   Copyright 2026
#

import pytest

from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_684_"


def test_issue684_move_media_file_withdrawn_after_hvo_refetch(target_sandbox):
    """MoveMediaFile raises FP_ParameterError and leaves the ICmFile alone."""
    entry = target_sandbox.LexEntry.Create(f"{TEST_PREFIX}entry")
    sense = target_sandbox.Senses.Create(entry, f"{TEST_PREFIX}gloss")
    try:
        ex_src = target_sandbox.Examples.Create(sense, f"{TEST_PREFIX}src")
        ex_dst = target_sandbox.Examples.Create(sense, f"{TEST_PREFIX}dst")
        media = target_sandbox.Media.Create(f"{TEST_PREFIX}probe.wav")
        bare_media = target_sandbox.Object(media.Hvo)

        with pytest.warns(DeprecationWarning):
            with pytest.raises(FP_ParameterError):
                target_sandbox.Examples.MoveMediaFile(bare_media, ex_src, ex_dst)

        # Re-query: the ICmFile still exists, and neither example gained media.
        assert target_sandbox.Object(media.Hvo) is not None
        with pytest.warns(DeprecationWarning):
            assert target_sandbox.Examples.GetMediaFiles(ex_src) == []
        with pytest.warns(DeprecationWarning):
            assert target_sandbox.Examples.GetMediaFiles(ex_dst) == []

        target_sandbox.Examples.Delete(ex_dst)
        target_sandbox.Examples.Delete(ex_src)
    finally:
        target_sandbox.LexEntry.Delete(entry)
