#
#   test_issue459_pronunciation_resolver_cast_live.py
#
#   Live gate for issue #459 PronunciationOperations HVO resolver casts.
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_459_"


@pytest.mark.requires_live_project
class TestIssue459PronunciationFormHvoGate:
    """
    GetForm resolves the pronunciation via __GetPronunciationObject and reads
    Form -- subtype-only on ILexPronunciation.
    """

    @pytest.mark.live_phase("PronunciationOperations", "read")
    def test_get_form_via_genuine_pronunciation_hvo(self, target_sandbox):
        sandbox = target_sandbox
        entry = sandbox.LexEntry.Create(f"{TEST_PREFIX}entry")
        try:
            pron = sandbox.Pronunciations.Create(entry, f"{TEST_PREFIX}ipa")
            hvo = pron.Hvo
            assert isinstance(hvo, int), (
                "test setup error: hvo must be a genuine Python int"
            )
            assert not hasattr(sandbox.Object(hvo), "Form"), (
                "precondition failed: Form reachable on bare ICmObject view "
                "-- re-derive the gate site"
            )

            form = sandbox.Pronunciations.GetForm(hvo)
            assert isinstance(form, str)
            assert TEST_PREFIX in form
        finally:
            sandbox.LexEntry.Delete(entry)
