#
#   test_issue836_cmmedia_cast_live.py
#
#   Live gate for issue #836: cast_to_concrete on CmMedia HVO from Object().
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import struct
import wave

import pytest

from flexicon import cast_to_concrete

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_836_"


def _write_wav(path):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(struct.pack("<8h", *range(8)))
    return str(path)


@pytest.mark.requires_live_project
class TestIssue836CmMediaCastLive:
    @pytest.mark.live_phase("cast_to_concrete", "read")
    def test_object_hvo_cast_exposes_media_file_ra(self, target_sandbox, tmp_path):
        entry = target_sandbox.LexEntry.Create(f"{TEST_PREFIX}entry")
        try:
            pron = target_sandbox.Pronunciations.Create(entry, f"{TEST_PREFIX}p")
            media = target_sandbox.Pronunciations.AddMediaFile(
                pron,
                _write_wav(tmp_path / f"{TEST_PREFIX}.wav"),
                label=f"{TEST_PREFIX}lbl",
            )
            media_hvo = media.Hvo
            bare = target_sandbox.Object(media_hvo)
            assert bare.ClassName == "CmMedia"
            assert not hasattr(bare, "MediaFileRA"), (
                "precondition failed: MediaFileRA reachable on bare Object() view "
                "-- re-derive the gate site"
            )

            concrete = cast_to_concrete(bare)
            assert concrete.ClassName == "CmMedia"
            assert hasattr(concrete, "MediaFileRA")
            assert concrete.MediaFileRA is not None
            assert concrete.MediaFileRA.ClassName == "CmFile"
            ws = target_sandbox.project.DefaultAnalWs
            assert concrete.Label.get_String(ws).Text == f"{TEST_PREFIX}lbl"
            print(
                f"[EVIDENCE-836] cast readback media_hvo={media_hvo} "
                f"MediaFileRA.Hvo={concrete.MediaFileRA.Hvo} "
                f"owner_pron_hvo={concrete.Owner.Hvo}"
            )

            target_sandbox.Pronunciations.Delete(pron)
        finally:
            target_sandbox.LexEntry.Delete(entry)
