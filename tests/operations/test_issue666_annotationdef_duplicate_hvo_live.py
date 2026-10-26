#
#   test_issue666_annotationdef_duplicate_hvo_live.py
#
#   Live verification for issue #666 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_666_"


class TestIssue666AnnotationDefDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("AnnotationDefOperations", "write")
    def test_duplicate_insert_after_raw_object_view(self, target_sandbox):
        op = target_sandbox.AnnotationDefs
        anno_list = target_sandbox.lp.AnnotationDefsOA
        assert anno_list is not None

        def_a = op.Create(f"{TEST_PREFIX}a", 0)
        def_b = op.Create(f"{TEST_PREFIX}b", 0)
        def_c = op.Create(f"{TEST_PREFIX}c", 0)
        try:
            raw_mid = target_sandbox.Object(def_b.Hvo)
            dup = op.Duplicate(raw_mid, insert_after=True, deep=False)

            order = [p.Hvo for p in anno_list.PossibilitiesOS]
            assert order.index(dup.Hvo) == order.index(def_b.Hvo) + 1

            op.Delete(dup)
            op.Delete(def_c)
            op.Delete(def_b)
            op.Delete(def_a)
        except Exception:
            for d in (def_a, def_b, def_c):
                try:
                    op.Delete(d)
                except Exception:
                    pass
            raise
