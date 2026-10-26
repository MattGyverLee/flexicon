#
#   test_issue706_naturalclass_segmentsrc_hvo_live.py
#
#   Live verification for issue #706 NaturalClass SegmentsRC HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_706_"


@pytest.mark.requires_live_project
class TestIssue706NaturalClassSegmentsRcHvoLive:
    """AddPhoneme/RemovePhoneme must not rely on Python proxy identity in SegmentsRC."""

    @pytest.mark.live_phase("NaturalClassOperations", "modify")
    def test_remove_phoneme_via_bare_object_view(self, target_sandbox):
        nc_ops = target_sandbox.NaturalClasses
        ph_ops = target_sandbox.Phonemes

        nc = nc_ops.Create(f"{TEST_PREFIX}nc", f"{TEST_PREFIX}NC")
        phoneme = ph_ops.Create(f"{TEST_PREFIX}p")
        try:
            nc_ops.AddPhoneme(nc, phoneme)
            assert len(nc_ops.GetPhonemes(nc)) == 1

            bare_phoneme = target_sandbox.Object(phoneme.Hvo)
            nc_ops.RemovePhoneme(nc, bare_phoneme)
            assert len(nc_ops.GetPhonemes(nc)) == 0
        finally:
            nc_ops.Delete(nc)
            ph_ops.Delete(phoneme)

    @pytest.mark.live_phase("NaturalClassOperations", "modify")
    def test_add_phoneme_skips_duplicate_for_bare_object_view(self, target_sandbox):
        nc_ops = target_sandbox.NaturalClasses
        ph_ops = target_sandbox.Phonemes

        nc = nc_ops.Create(f"{TEST_PREFIX}nc2", f"{TEST_PREFIX}N2")
        phoneme = ph_ops.Create(f"{TEST_PREFIX}q")
        try:
            nc_ops.AddPhoneme(nc, phoneme)
            assert len(nc_ops.GetPhonemes(nc)) == 1

            bare_phoneme = target_sandbox.Object(phoneme.Hvo)
            nc_ops.AddPhoneme(nc, bare_phoneme)
            assert len(nc_ops.GetPhonemes(nc)) == 1
        finally:
            nc_ops.Delete(nc)
            ph_ops.Delete(phoneme)
