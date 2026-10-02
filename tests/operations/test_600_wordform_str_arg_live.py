#
#   test_600_wordform_str_arg_live.py
#
#   Live gate for issue 600: str passed where a wordform is expected
#   raises FP_ParameterError against a real LCM, and the supported
#   Find -> GetForm flow still works.
#
#   Copyright 2026
#

import pytest

from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project


class TestIssue600WordformStrArg:
    @pytest.mark.live_phase("WordformOperations", "read")
    def test_str_arg_raises_typed_error_and_find_flow_works(self, target_sandbox):
        wfs = target_sandbox.Wordforms
        wf = wfs.Create("TEST_issue600_wordform")
        try:
            with pytest.raises(FP_ParameterError) as exc:
                wfs.GetForm("TEST_issue600_wordform")
            assert "IWfiWordform" in str(exc.value)
            with pytest.raises(FP_ParameterError):
                wfs.SetForm("TEST_issue600_wordform", "x")

            # Supported flow: Find then GetForm, read back from the LCM.
            found = wfs.Find("TEST_issue600_wordform")
            assert found is not None
            assert wfs.GetForm(found) == "TEST_issue600_wordform"
            assert wfs.GetForm(wf.Hvo) == "TEST_issue600_wordform"
        finally:
            wfs.Delete(wf)
        assert wfs.Find("TEST_issue600_wordform") is None
