#
#   test_issue831_example_media_offline.py
#
#   Offline checks for issue #831: the five ExampleOperations media methods
#   are withdrawn (ILexExampleSentence has no MediaFilesOS).
#
#   Copyright 2026
#

import warnings
from unittest.mock import MagicMock

import pytest

from flexicon.code.FLExProject import FP_NullParameterError, FP_ParameterError
from flexicon.code.Lexicon.ExampleOperations import (
    ExampleOperations,
    _EXAMPLE_MEDIA_WITHDRAWN,
)


@pytest.fixture
def ops_and_project():
    project = MagicMock()
    project.writeEnabled = True
    return ExampleOperations(project), project


def _writer_calls(ops):
    example = MagicMock(name="example")
    other = MagicMock(name="other_example")
    media = MagicMock(name="media")
    return {
        "AddMediaFile": lambda: ops.AddMediaFile(example, "/x/a.wav", label="L"),
        "RemoveMediaFile": lambda: ops.RemoveMediaFile(example, media),
        "MoveMediaFile": lambda: ops.MoveMediaFile(media, example, other),
    }


@pytest.mark.parametrize("name", ["AddMediaFile", "RemoveMediaFile", "MoveMediaFile"])
def test_writers_warn_then_raise_without_touching_anything(ops_and_project, name):
    ops, project = ops_and_project
    call = _writer_calls(ops)[name]
    with pytest.warns(DeprecationWarning):
        with pytest.raises(FP_ParameterError):
            call()
    project.Media.CopyToProject.assert_not_called()
    assert project.method_calls == [], project.method_calls
    project.project.ServiceLocator.assert_not_called()


@pytest.mark.parametrize("name", ["AddMediaFile", "RemoveMediaFile", "MoveMediaFile"])
def test_writers_raise_even_when_project_is_read_only(ops_and_project, name):
    ops, project = ops_and_project
    project.writeEnabled = False
    with pytest.warns(DeprecationWarning):
        with pytest.raises(FP_ParameterError):
            _writer_calls(ops)[name]()


def test_get_media_files_warns_and_returns_empty(ops_and_project):
    ops, project = ops_and_project
    example = MagicMock(name="example")
    example.MediaFilesOS = [object(), object()]  # must never be read
    with pytest.warns(DeprecationWarning):
        assert ops.GetMediaFiles(example) == []
    assert project.method_calls == []


def test_get_media_count_warns_and_returns_zero(ops_and_project):
    ops, project = ops_and_project
    example = MagicMock(name="example")
    example.MediaFilesOS.Count = 7  # must never be read
    with pytest.warns(DeprecationWarning):
        assert ops.GetMediaCount(example) == 0
    assert project.method_calls == []


@pytest.mark.parametrize("name", ["GetMediaFiles", "GetMediaCount"])
def test_getters_keep_null_check(ops_and_project, name):
    ops, _ = ops_and_project
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        with pytest.raises(FP_NullParameterError):
            getattr(ops, name)(None)


def test_withdrawal_message_content():
    msg = _EXAMPLE_MEDIA_WITHDRAWN
    assert "no media collection" in msg
    assert "audio writing-system alternative" in msg
    assert "SetExample(example, text, wsHandle)" in msg
    assert "4.14.0" in msg
    assert "removed in 5.0" in msg
    assert "LinkedFiles" not in msg


def test_warning_message_is_the_shared_constant(ops_and_project):
    ops, _ = ops_and_project
    with pytest.warns(DeprecationWarning) as rec:
        ops.GetMediaCount(MagicMock())
    assert str(rec[0].message) == _EXAMPLE_MEDIA_WITHDRAWN
