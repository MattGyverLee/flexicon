#
#   test_issue457_lexsense_resolver_cast_live.py
#
#   Live gate for issue #457 LexSenseOperations HVO resolver casts.
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_457_"


@pytest.mark.requires_live_project
class TestIssue457LexSenseGlossHvoGate:
    """
    GetGloss resolves the sense via __GetSenseObject and reads Gloss --
    subtype-only on ILexSense.
    """

    @pytest.mark.live_phase("LexSenseOperations", "read")
    def test_get_gloss_via_genuine_sense_hvo(self, target_sandbox):
        sandbox = target_sandbox
        entry = sandbox.LexEntry.Create(f"{TEST_PREFIX}entry")
        try:
            sense = sandbox.Senses.Create(entry, f"{TEST_PREFIX}sense")
            sandbox.Senses.SetGloss(sense, f"{TEST_PREFIX}gloss")
            hvo = sense.Hvo
            assert isinstance(hvo, int), (
                "test setup error: hvo must be a genuine Python int"
            )
            assert not hasattr(sandbox.Object(hvo), "Gloss"), (
                "precondition failed: Gloss reachable on bare ICmObject view "
                "-- re-derive the gate site"
            )

            gloss = sandbox.Senses.GetGloss(hvo)
            assert isinstance(gloss, str)
            assert TEST_PREFIX in gloss
        finally:
            sandbox.LexEntry.Delete(entry)
