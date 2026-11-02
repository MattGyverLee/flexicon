#
#   test_issue686_pronunciation_movemedia_hvo_live.py
#
#   Live verification for issue #686 Pronunciation MoveMediaFile HVO membership
#   lookup, reworked for issue #828 (MediaFilesOS holds ICmMedia, not ICmFile).
#
#   Copyright 2026
#

import struct
import wave

import pytest

from flexicon import cast_to_concrete

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_686_"


def _write_wav(path):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(struct.pack("<8h", *range(8)))
    return str(path)


def _hvos(project, pron_hvo):
    pron = cast_to_concrete(project.Object(pron_hvo))
    return [m.Hvo for m in pron.MediaFilesOS]


@pytest.mark.parametrize("handle_kind", ["bare_icmmedia", "icmfile"])
def test_issue686_move_media_file_after_hvo_refetch(target_sandbox, tmp_path, handle_kind):
    """MoveMediaFile succeeds for a bare Object(hvo) ICmMedia and for its ICmFile."""
    entry = target_sandbox.LexEntry.Create(f"{TEST_PREFIX}entry_{handle_kind}")
    try:
        pron_src = target_sandbox.Pronunciations.Create(entry, f"{TEST_PREFIX}src")
        pron_dst = target_sandbox.Pronunciations.Create(entry, f"{TEST_PREFIX}dst")
        src_hvo, dst_hvo = pron_src.Hvo, pron_dst.Hvo
        wav = _write_wav(tmp_path / f"{TEST_PREFIX}{handle_kind}.wav")
        media = target_sandbox.Pronunciations.AddMediaFile(pron_src, wav)
        media_hvo = media.Hvo
        file_hvo = media.MediaFileRA.Hvo

        if handle_kind == "bare_icmmedia":
            handle = target_sandbox.Object(media_hvo)
        else:
            handle = media.MediaFileRA

        moved = target_sandbox.Pronunciations.MoveMediaFile(handle, pron_src, pron_dst)
        assert moved is True

        assert media_hvo not in _hvos(target_sandbox, src_hvo)
        assert media_hvo in _hvos(target_sandbox, dst_hvo)
        # Re-parented, not recreated: same ICmMedia still references the file.
        dst_items = cast_to_concrete(target_sandbox.Object(dst_hvo)).MediaFilesOS
        moved_item = [m for m in dst_items if m.Hvo == media_hvo][0]
        assert moved_item.MediaFileRA.Hvo == file_hvo
        print(
            f"[EVIDENCE-686] kind={handle_kind} readback media_hvo={moved_item.Hvo} "
            f"MediaFileRA.Hvo={moved_item.MediaFileRA.Hvo} "
            f"owner_pron_hvo={moved_item.Owner.Hvo} src_pron_hvo={src_hvo} "
            f"dst_pron_hvo={dst_hvo} src_media_hvos={_hvos(target_sandbox, src_hvo)} "
            f"dst_media_hvos={_hvos(target_sandbox, dst_hvo)}"
        )

        target_sandbox.Pronunciations.Delete(pron_dst)
        target_sandbox.Pronunciations.Delete(pron_src)
    finally:
        target_sandbox.LexEntry.Delete(entry)
