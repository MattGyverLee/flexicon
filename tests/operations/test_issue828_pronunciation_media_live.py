#
#   test_issue828_pronunciation_media_live.py
#
#   Live verification for issue #828: PronunciationOperations media methods
#   must use ICmMedia (the element type of ILexPronunciation.MediaFilesOS).
#
#   Copyright 2026
#

import struct
import wave

import pytest

from flexicon import cast_to_concrete

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_828_"


def _write_wav(path):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(struct.pack("<8h", *range(8)))
    return str(path)


def _media(project, pron_hvo):
    return list(cast_to_concrete(project.Object(pron_hvo)).MediaFilesOS)


class TestIssue828PronunciationMediaLive:
    def test_add_media_file_returns_icmmedia_with_label(self, target_sandbox, tmp_path):
        entry = target_sandbox.LexEntry.Create(f"{TEST_PREFIX}add")
        try:
            pron = target_sandbox.Pronunciations.Create(entry, f"{TEST_PREFIX}p")
            hvo = pron.Hvo
            wav = _write_wav(tmp_path / f"{TEST_PREFIX}a.wav")
            ret = target_sandbox.Pronunciations.AddMediaFile(pron, wav, label=f"{TEST_PREFIX}lbl")

            items = _media(target_sandbox, hvo)
            assert [m.Hvo for m in items] == [ret.Hvo]
            fetched = items[0]
            assert fetched.ClassName == "CmMedia"
            assert fetched.MediaFileRA is not None
            assert fetched.MediaFileRA.ClassName == "CmFile"
            ws = target_sandbox.project.DefaultAnalWs
            assert fetched.Label.get_String(ws).Text == f"{TEST_PREFIX}lbl"
            print(
                f"[EVIDENCE-828] add readback media_hvo={fetched.Hvo} "
                f"MediaFileRA.Hvo={fetched.MediaFileRA.Hvo} owner_pron_hvo={fetched.Owner.Hvo}"
            )

            target_sandbox.Pronunciations.Delete(pron)
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.parametrize("handle_kind", ["icmmedia", "hvo", "icmfile"])
    def test_remove_media_file(self, target_sandbox, tmp_path, handle_kind):
        entry = target_sandbox.LexEntry.Create(f"{TEST_PREFIX}rm_{handle_kind}")
        try:
            pron = target_sandbox.Pronunciations.Create(entry, f"{TEST_PREFIX}p")
            hvo = pron.Hvo
            keep = target_sandbox.Pronunciations.AddMediaFile(
                pron, _write_wav(tmp_path / f"{TEST_PREFIX}keep.wav"))
            gone = target_sandbox.Pronunciations.AddMediaFile(
                pron, _write_wav(tmp_path / f"{TEST_PREFIX}gone.wav"))
            keep_hvo, gone_hvo = keep.Hvo, gone.Hvo
            handle = {
                "icmmedia": gone,
                "hvo": gone_hvo,
                "icmfile": gone.MediaFileRA,
            }[handle_kind]

            target_sandbox.Pronunciations.RemoveMediaFile(pron, handle)

            remaining = _media(target_sandbox, hvo)
            assert [m.Hvo for m in remaining] == [keep_hvo]
            print(
                f"[EVIDENCE-828] remove kind={handle_kind} removed_media_hvo={gone_hvo} "
                f"remaining_media_hvo={remaining[0].Hvo} "
                f"remaining_MediaFileRA.Hvo={remaining[0].MediaFileRA.Hvo} "
                f"owner_pron_hvo={remaining[0].Owner.Hvo}"
            )

            target_sandbox.Pronunciations.Delete(pron)
        finally:
            target_sandbox.LexEntry.Delete(entry)

    def test_remove_unrelated_icmfile_raises(self, target_sandbox, tmp_path):
        from flexicon import FP_ParameterError

        entry = target_sandbox.LexEntry.Create(f"{TEST_PREFIX}bad")
        try:
            p1 = target_sandbox.Pronunciations.Create(entry, f"{TEST_PREFIX}p1")
            p2 = target_sandbox.Pronunciations.Create(entry, f"{TEST_PREFIX}p2")
            m2 = target_sandbox.Pronunciations.AddMediaFile(
                p2, _write_wav(tmp_path / f"{TEST_PREFIX}x.wav"))
            with pytest.raises(FP_ParameterError):
                target_sandbox.Pronunciations.RemoveMediaFile(p1, m2.MediaFileRA)
            assert len(_media(target_sandbox, p2.Hvo)) == 1
            target_sandbox.Pronunciations.Delete(p2)
            target_sandbox.Pronunciations.Delete(p1)
        finally:
            target_sandbox.LexEntry.Delete(entry)

    def test_pronunciation_duplicate_deep_copies_media(self, target_sandbox, tmp_path):
        entry = target_sandbox.LexEntry.Create(f"{TEST_PREFIX}pdup")
        try:
            pron = target_sandbox.Pronunciations.Create(entry, f"{TEST_PREFIX}p")
            src = target_sandbox.Pronunciations.AddMediaFile(
                pron, _write_wav(tmp_path / f"{TEST_PREFIX}d.wav"), label=f"{TEST_PREFIX}dl")
            src_media_hvo, file_hvo = src.Hvo, src.MediaFileRA.Hvo

            dup = target_sandbox.Pronunciations.Duplicate(pron, deep=True)

            copies = _media(target_sandbox, dup.Hvo)
            assert len(copies) == 1
            assert copies[0].Hvo != src_media_hvo
            assert copies[0].MediaFileRA.Hvo == file_hvo
            ws = target_sandbox.project.DefaultAnalWs
            assert copies[0].Label.get_String(ws).Text == f"{TEST_PREFIX}dl"
            # Source untouched
            assert [m.Hvo for m in _media(target_sandbox, pron.Hvo)] == [src_media_hvo]
            print(
                f"[EVIDENCE-828] pron-dup readback src_media_hvo={src_media_hvo} "
                f"copy_media_hvo={copies[0].Hvo} copy_MediaFileRA.Hvo={copies[0].MediaFileRA.Hvo} "
                f"copy_owner_pron_hvo={copies[0].Owner.Hvo} dup_pron_hvo={dup.Hvo}"
            )

            target_sandbox.Pronunciations.Delete(dup)
            target_sandbox.Pronunciations.Delete(pron)
        finally:
            target_sandbox.LexEntry.Delete(entry)

    def test_lexentry_duplicate_deep_copies_pronunciation_media(self, target_sandbox, tmp_path):
        entry = target_sandbox.LexEntry.Create(f"{TEST_PREFIX}edup")
        dup_entry = None
        try:
            pron = target_sandbox.Pronunciations.Create(entry, f"{TEST_PREFIX}p")
            src = target_sandbox.Pronunciations.AddMediaFile(
                pron, _write_wav(tmp_path / f"{TEST_PREFIX}e.wav"), label=f"{TEST_PREFIX}el")
            src_media_hvo, file_hvo = src.Hvo, src.MediaFileRA.Hvo

            dup_entry = target_sandbox.LexEntry.Duplicate(entry, deep=True)

            dup_prons = list(cast_to_concrete(target_sandbox.Object(dup_entry.Hvo)).PronunciationsOS)
            assert len(dup_prons) == 1
            copies = _media(target_sandbox, dup_prons[0].Hvo)
            assert len(copies) == 1
            assert copies[0].Hvo != src_media_hvo
            assert copies[0].MediaFileRA.Hvo == file_hvo
            ws = target_sandbox.project.DefaultAnalWs
            assert copies[0].Label.get_String(ws).Text == f"{TEST_PREFIX}el"
            print(
                f"[EVIDENCE-828] entry-dup readback src_media_hvo={src_media_hvo} "
                f"copy_media_hvo={copies[0].Hvo} copy_MediaFileRA.Hvo={copies[0].MediaFileRA.Hvo} "
                f"copy_owner_pron_hvo={copies[0].Owner.Hvo}"
            )
        finally:
            if dup_entry is not None:
                target_sandbox.LexEntry.Delete(dup_entry)
            target_sandbox.LexEntry.Delete(entry)
