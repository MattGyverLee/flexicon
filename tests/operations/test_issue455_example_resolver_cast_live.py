#
#   test_issue455_example_resolver_cast_live.py
#
#   Issue #455: HVO-entry live gate for ExampleOperations publication
#   helpers that read DoNotPublishInRC on ILexExampleSentence.
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_455_"


@pytest.mark.requires_live_project
class TestIssue455ExampleDoNotPublishInHvoGate:
    """
    AddDoNotPublishIn resolves the example via __GetExampleObject and
    reads DoNotPublishInRC -- subtype-only on ILexExampleSentence.
    """

    @pytest.mark.live_phase("ExampleOperations", "read")
    def test_get_do_not_publish_in_via_genuine_example_hvo(self, target_sandbox):
        sandbox = target_sandbox
        entry = sandbox.LexEntry.Create(f"{TEST_PREFIX}entry")
        try:
            sense = sandbox.Senses.Create(entry, f"{TEST_PREFIX}sense")
            example = sandbox.Examples.Create(sense, f"{TEST_PREFIX}ex")
            hvo = example.Hvo
            assert isinstance(hvo, int), (
                "test setup error: hvo must be a genuine Python int"
            )
            assert not hasattr(sandbox.Object(hvo), "DoNotPublishInRC"), (
                "precondition failed: DoNotPublishInRC reachable on bare "
                "ICmObject view -- re-derive the gate site"
            )

            pubs = sandbox.Examples.GetDoNotPublishIn(hvo)
            assert isinstance(pubs, list)
        finally:
            sandbox.LexEntry.Delete(entry)
