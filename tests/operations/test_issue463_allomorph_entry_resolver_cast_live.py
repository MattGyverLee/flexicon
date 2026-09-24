#
#   test_issue463_allomorph_entry_resolver_cast_live.py
#
#   Live gate for issue #463 AllomorphOperations __GetEntryObject cast.
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_463_"


@pytest.mark.requires_live_project
class TestIssue463AllomorphCreateEntryHvoGate:
    """
    Create resolves the entry via __GetEntryObject and reads LexemeFormOA /
    AlternateFormsOS -- subtype-only on ILexEntry.
    """

    @pytest.mark.live_phase("AllomorphOperations", "modify")
    def test_create_via_genuine_entry_hvo(self, target_sandbox):
        sandbox = target_sandbox
        entry = sandbox.LexEntry.Create(f"{TEST_PREFIX}entry")
        try:
            entry_hvo = entry.Hvo
            assert isinstance(entry_hvo, int), (
                "test setup error: entry_hvo must be a genuine Python int"
            )
            assert not hasattr(sandbox.Object(entry_hvo), "AlternateFormsOS"), (
                "precondition failed: AlternateFormsOS reachable on bare "
                "ICmObject view -- re-derive the gate site"
            )

            allo = sandbox.Allomorphs.Create(
                entry_hvo, f"{TEST_PREFIX}form", morphType="suffix"
            )
            assert allo is not None
            form_text = sandbox.Allomorphs.GetForm(allo)
            assert TEST_PREFIX in form_text
        finally:
            sandbox.LexEntry.Delete(entry)
