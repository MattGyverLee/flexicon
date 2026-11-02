#
#   test_issue828_pronunciation_media_offline.py
#
#   Offline guards for issue #828 media methods: a rejected AddMediaFile must
#   not copy anything, and RemoveMediaFile must raise (not return silently)
#   when the object has no media collection.
#
#   Copyright 2026
#

from unittest.mock import MagicMock, patch

import pytest

from flexicon import FP_ParameterError
from flexicon.code.Lexicon.PronunciationOperations import PronunciationOperations

_RESOLVE = "_PronunciationOperations__GetPronunciationObject"


class _NoMedia:
    """Stand-in pronunciation that exposes no MediaFilesOS."""


def _ops():
    project = MagicMock()
    project.writeEnabled = True
    return PronunciationOperations(project), project


def test_rejected_add_media_file_does_not_copy(tmp_path):
    ops, project = _ops()
    wav = tmp_path / "x.wav"
    wav.write_bytes(b"RIFF")
    with patch.object(PronunciationOperations, _RESOLVE, return_value=_NoMedia()):
        with pytest.raises(FP_ParameterError, match="does not support media files"):
            ops.AddMediaFile(1234, str(wav))
    project.Media.CopyToProject.assert_not_called()


def test_remove_media_file_raises_when_no_media_collection():
    ops, _project = _ops()
    with patch.object(PronunciationOperations, _RESOLVE, return_value=_NoMedia()):
        with pytest.raises(FP_ParameterError, match="does not support media files"):
            ops.RemoveMediaFile(1234, 5678)
