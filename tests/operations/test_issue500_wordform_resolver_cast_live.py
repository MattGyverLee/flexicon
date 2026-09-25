#
#   test_issue500_wordform_resolver_cast_live.py
#
#   Live gate for issue #500 WordformOperations HVO resolver cast.
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project


@pytest.mark.requires_live_project
class TestIssue500WordformGetFormHvoGate:
    """
    GetForm resolves via __ResolveWordform and reads Form -- subtype-only on
    IWfiWordform.
    """

    @pytest.mark.live_phase("WordformOperations", "read")
    def test_get_form_via_genuine_wordform_hvo(self, target_sandbox):
        sandbox = target_sandbox
        wf = sandbox.Wordforms.Create("TEST_issue500_wordform")
        try:
            hvo = wf.Hvo
            assert isinstance(hvo, int), (
                "test setup error: hvo must be a genuine Python int"
            )
            bare = sandbox.Object(hvo)
            assert not hasattr(bare, "Form"), (
                "precondition failed: Form reachable on bare ICmObject view "
                "-- re-derive the gate site"
            )

            by_obj = sandbox.Wordforms.GetForm(wf)
            by_hvo = sandbox.Wordforms.GetForm(hvo)
            assert by_hvo == by_obj
            assert by_hvo == "TEST_issue500_wordform"
        finally:
            sandbox.Wordforms.Delete(wf)
