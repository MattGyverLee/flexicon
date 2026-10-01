#
#   test_issue597_variant_duplicate_hvo_live.py
#
#   Live verification for issue #597 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_597_"


def _first_variant_type(project):
    for vtype in project.Variants.GetAllTypes():
        return vtype
    return None


class TestIssue597VariantDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("VariantOperations", "write")
    def test_duplicate_insert_after_raw_object_view(self, target_sandbox):
        vtype = _first_variant_type(target_sandbox)
        if vtype is None:
            pytest.skip("Project defines zero variant types")

        entry = target_sandbox.LexEntry.Create(f"{TEST_PREFIX}entry")
        try:
            form_a = f"{TEST_PREFIX}a"
            form_b = f"{TEST_PREFIX}b"
            form_c = f"{TEST_PREFIX}c"
            ref_a = target_sandbox.Variants.Create(entry, form_a, vtype)
            ref_b = target_sandbox.Variants.Create(entry, form_b, vtype)
            ref_c = target_sandbox.Variants.Create(entry, form_c, vtype)

            raw_mid = target_sandbox.Object(ref_b.Hvo)
            dup = target_sandbox.Variants.Duplicate(
                raw_mid, insert_after=True, deep=False
            )

            order = [ref.Hvo for ref in entry.EntryRefsOS]
            assert order.index(dup.Hvo) == order.index(ref_b.Hvo) + 1

            target_sandbox.Variants.Delete(dup)
            target_sandbox.Variants.Delete(ref_c)
            target_sandbox.Variants.Delete(ref_b)
            target_sandbox.Variants.Delete(ref_a)
        finally:
            target_sandbox.LexEntry.Delete(entry)
