#
#   test_issue831_example_media_live.py
#
#   Live verification for issue #831: the ExampleOperations media methods
#   are withdrawn. AddMediaFile used to copy a file into LinkedFiles and
#   create an ICmFile before raising (an orphan on every call). It must now
#   raise before touching anything. Runs on the target_sandbox tempdir copy.
#
#   Copyright 2026
#

import os
import struct
import wave

import pytest

from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_831_"


def _icmfile_count(project):
    from SIL.LCModel import ICmFileRepository

    return sum(1 for _ in project.ObjectsIn(ICmFileRepository))


def _audio_listing(project):
    root = project.lp.LinkedFilesRootDir
    folder = os.path.join(str(root), "AudioVisual")
    if not os.path.isdir(folder):
        return None
    return sorted(os.listdir(folder))


def _multistring_snapshot(example):
    from SIL.LCModel import ILexExampleSentence

    ms = ILexExampleSentence(example).Example
    snap = {}
    for ws in ms.AvailableWritingSystemIds:
        snap[int(ws)] = ms.get_String(ws).Text
    return snap


def _write_wav(path):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(struct.pack("<8h", *range(8)))


def test_issue831_example_media_methods_withdrawn_and_inert(target_sandbox, tmp_path):
    project = target_sandbox
    wav = tmp_path / "probe831.wav"
    _write_wav(wav)

    entry = project.LexEntry.Create(f"{TEST_PREFIX}entry")
    sense = project.Senses.Create(entry, f"{TEST_PREFIX}gloss")
    try:
        example = project.Examples.Create(sense, f"{TEST_PREFIX}example")
        other = project.Examples.Create(sense, f"{TEST_PREFIX}other")
        hvo = example.Hvo
        other_hvo = other.Hvo
        media_probe = project.Media.Create(f"{TEST_PREFIX}probe.wav")

        before_files = _icmfile_count(project)
        before_dir = _audio_listing(project)
        before_ms = _multistring_snapshot(example)
        print(f"[EVIDENCE] example_hvo={hvo} icmfile_before={before_files} "
              f"audiovisual_before={before_dir} example_before={before_ms}")

        with pytest.warns(DeprecationWarning):
            with pytest.raises(FP_ParameterError):
                project.Examples.AddMediaFile(example, str(wav), label="probe")

        fetched = project.Object(hvo)
        after_files = _icmfile_count(project)
        after_dir = _audio_listing(project)
        after_ms = _multistring_snapshot(fetched)
        print(f"[EVIDENCE] example_hvo={hvo} icmfile_after_add={after_files} "
              f"audiovisual_after_add={after_dir} example_after_add={after_ms}")
        assert after_files == before_files
        assert after_dir == before_dir
        assert after_ms == before_ms

        with pytest.warns(DeprecationWarning):
            with pytest.raises(FP_ParameterError):
                project.Examples.RemoveMediaFile(fetched, media_probe.Hvo)
        with pytest.warns(DeprecationWarning):
            with pytest.raises(FP_ParameterError):
                project.Examples.MoveMediaFile(
                    project.Object(media_probe.Hvo), fetched, project.Object(other_hvo)
                )

        fetched = project.Object(hvo)
        final_files = _icmfile_count(project)
        final_dir = _audio_listing(project)
        final_ms = _multistring_snapshot(fetched)
        with pytest.warns(DeprecationWarning):
            media = project.Examples.GetMediaFiles(fetched)
        with pytest.warns(DeprecationWarning):
            count = project.Examples.GetMediaCount(fetched)
        print(f"[EVIDENCE] example_hvo={hvo} icmfile_final={final_files} "
              f"audiovisual_final={final_dir} example_final={final_ms} "
              f"get={media} count={count}")
        assert final_files == before_files
        assert final_dir == before_dir
        assert final_ms == before_ms
        assert media == []
        assert count == 0

        project.Examples.Delete(other)
        project.Examples.Delete(example)
    finally:
        project.LexEntry.Delete(entry)
