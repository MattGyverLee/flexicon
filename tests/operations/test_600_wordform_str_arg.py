#
#   test_600_wordform_str_arg.py
#
#   Offline test for issue 600: WordformOperations methods given a str
#   (or other wrong type) must raise FP_ParameterError, not a raw
#   AttributeError.
#
#   Copyright 2026
#

import pytest
from unittest.mock import MagicMock

from flexicon.code.FLExProject import FP_ParameterError
from flexicon.code.TextsWords.WordformOperations import WordformOperations


def _ops():
    ops = object.__new__(WordformOperations)
    ops.project = MagicMock()
    return ops


class TestResolveWordformRejectsWrongTypes:
    @pytest.mark.parametrize("bad", ["running", "", None, 1.5, ["x"], b"x"])
    def test_resolver_wrong_type_raises_fp_parameter_error(self, bad):
        with pytest.raises(FP_ParameterError) as exc:
            _ops()._WordformOperations__ResolveWordform(bad)
        assert "IWfiWordform" in str(exc.value)
        assert "Wordforms.Find" in str(exc.value)

    def test_get_form_str_raises_fp_parameter_error(self):
        with pytest.raises(FP_ParameterError):
            _ops().GetForm("running")

    def test_resolver_accepts_wordform_like_object(self):
        wf = MagicMock()
        wf.ClassName = "Other"
        assert _ops()._WordformOperations__ResolveWordform(wf) is wf
