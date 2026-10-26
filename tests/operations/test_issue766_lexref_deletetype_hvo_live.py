#
#   test_issue766_lexref_deletetype_hvo_live.py
#
#   Live gate for issue #766 DeleteType HVO membership on ReferencesOA.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_766_"


@pytest.mark.requires_live_project
class TestIssue766LexRefDeleteTypeHvoLive:
    """DeleteType must detach ref type when passed Object(hvo) after creation."""

    @pytest.mark.live_phase("LexReferenceOperations", "delete")
    def test_delete_type_via_resolved_hvo(self, target_sandbox):
        ref_ops = target_sandbox.LexReferences
        name = f"{TEST_PREFIX}relation"

        created = None
        try:
            created = ref_ops.CreateType(name, "Symmetric")
            assert created is not None

            resolved = target_sandbox.Object(int(created.Hvo))
            ref_ops.DeleteType(resolved)

            assert ref_ops.FindType(name) is None
        finally:
            if created is not None and ref_ops.FindType(name) is not None:
                try:
                    ref_ops.DeleteType(created)
                except Exception:
                    pass
