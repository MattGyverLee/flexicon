#
#   test_issue768_variant_delete_hvo_live.py
#
#   Live verification for issue #768 Delete EntryRefsOS HVO membership.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_768_"


def _first_variant_type(project):
    for vtype in project.Variants.GetAllTypes():
        return vtype
    return None


class TestIssue768VariantDeleteHvoLive:
    """Delete must detach when passing raw Object(hvo) after create."""

    @pytest.mark.live_phase("VariantOperations", "write")
    def test_delete_raw_object_view(self, target_sandbox):
        vtype = _first_variant_type(target_sandbox)
        if vtype is None:
            pytest.skip("Project defines zero variant types")

        entry = target_sandbox.LexEntry.Create(f"{TEST_PREFIX}entry")
        try:
            form = f"{TEST_PREFIX}form"
            ref = target_sandbox.Variants.Create(entry, form, vtype)
            assert len(list(entry.EntryRefsOS)) == 1

            raw = target_sandbox.Object(ref.Hvo)
            target_sandbox.Variants.Delete(raw)

            assert len(list(entry.EntryRefsOS)) == 0
        finally:
            target_sandbox.LexEntry.Delete(entry)
