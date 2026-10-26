#
#   test_issue648_pos_duplicate_hvo_live.py
#
#   Live verification for issue #648 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest
from SIL.LCModel import IPartOfSpeech

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_648_"


class TestIssue648PosDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("POSOperations", "write")
    def test_duplicate_top_level_insert_after_raw_object_view(self, target_sandbox):
        sandbox = target_sandbox
        pos_a = sandbox.POS.Create(f"{TEST_PREFIX}a", "648a")
        pos_b = sandbox.POS.Create(f"{TEST_PREFIX}b", "648b")
        pos_c = sandbox.POS.Create(f"{TEST_PREFIX}c", "648c")
        dup = None
        try:
            raw_mid = sandbox.Object(pos_b.Hvo)
            dup = sandbox.POS.Duplicate(raw_mid, insert_after=True, deep=False)

            pos_list = sandbox.project.lp.PartsOfSpeechOA.PossibilitiesOS
            order = [p.Hvo for p in pos_list]
            assert order.index(dup.Hvo) == order.index(pos_b.Hvo) + 1
        finally:
            if dup is not None:
                sandbox.POS.Delete(dup)
            sandbox.POS.Delete(pos_c)
            sandbox.POS.Delete(pos_b)
            sandbox.POS.Delete(pos_a)

    @pytest.mark.live_phase("POSOperations", "write")
    def test_duplicate_subcategory_insert_after_raw_object_view(self, target_sandbox):
        sandbox = target_sandbox
        parent = sandbox.POS.Create(f"{TEST_PREFIX}parent", "648p")
        sub_a = sandbox.POS.AddSubcategory(parent, f"{TEST_PREFIX}s0", "648s0")
        sub_b = sandbox.POS.AddSubcategory(parent, f"{TEST_PREFIX}s1", "648s1")
        sub_c = sandbox.POS.AddSubcategory(parent, f"{TEST_PREFIX}s2", "648s2")
        dup = None
        try:
            raw_mid = sandbox.Object(sub_b.Hvo)
            dup = sandbox.POS.Duplicate(raw_mid, insert_after=True, deep=False)

            parent_pos = IPartOfSpeech(parent)
            order = [s.Hvo for s in parent_pos.SubPossibilitiesOS]
            assert order.index(dup.Hvo) == order.index(sub_b.Hvo) + 1
        finally:
            if dup is not None:
                sandbox.POS.Delete(dup)
            sandbox.POS.RemoveSubcategory(parent, sub_c)
            sandbox.POS.RemoveSubcategory(parent, sub_b)
            sandbox.POS.RemoveSubcategory(parent, sub_a)
            sandbox.POS.Delete(parent)
