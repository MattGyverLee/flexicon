#
#   test_issue798_phoneme_delete_hvo_live.py
#
#   Live gate for issue #798 Delete HVO membership on PhonemesOC.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_798_"


@pytest.mark.requires_live_project
class TestIssue798PhonemeDeleteHvoLive:
    """Delete must remove the phoneme when passed Object(hvo) after creation."""

    @pytest.mark.live_phase("PhonemeOperations", "delete")
    def test_delete_via_resolved_hvo(self, target_sandbox):
        phoneme_ops = target_sandbox.Phonemes
        representation = f"{TEST_PREFIX}/z/"

        phoneme = None
        try:
            if phoneme_ops.Exists(representation):
                existing = phoneme_ops.Find(representation)
                if existing is not None:
                    phoneme_ops.Delete(existing)

            phoneme = phoneme_ops.Create(representation)
            assert phoneme is not None
            phoneme_hvo = int(phoneme.Hvo)

            resolved = target_sandbox.Object(phoneme_hvo)
            phoneme_ops.Delete(resolved)

            assert not phoneme_ops.Exists(representation)
            for remaining in phoneme_ops.GetAll():
                assert int(remaining.Hvo) != phoneme_hvo
            phoneme = None
        finally:
            if phoneme is not None:
                try:
                    phoneme_ops.Delete(phoneme)
                except Exception:
                    pass
