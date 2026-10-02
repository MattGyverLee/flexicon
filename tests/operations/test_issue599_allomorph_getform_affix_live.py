#
#   test_issue599_allomorph_getform_affix_live.py
#
#   Live gate for issue #599: AllomorphOperations.GetForm on affix
#   allomorphs (shared resolver __GetAllomorphObject).
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_599_"


class TestIssue599GetFormAffix:
    """GetForm must work for stem and affix allomorphs, in every input shape."""

    @pytest.mark.live_phase("AllomorphOperations", "read")
    def test_getform_on_affix_allomorph_all_input_shapes(self, target_sandbox):
        sandbox = target_sandbox
        ops = sandbox.Allomorphs
        entry = sandbox.LexEntry.Create(f"{TEST_PREFIX}entry")
        try:
            affix = ops.Create(entry, f"{TEST_PREFIX}suf", morphType="suffix")
            stem = ops.Create(entry, f"{TEST_PREFIX}stem", morphType="stem")
            assert affix is not None and stem is not None

            # Read back what the LCM actually holds.
            affix_obj = sandbox.Object(affix.Hvo)
            stem_obj = sandbox.Object(stem.Hvo)
            assert affix_obj.ClassName == "MoAffixAllomorph"
            assert stem_obj.ClassName == "MoStemAllomorph"

            # Raw object, HVO, and GetAll() wrapper shapes.
            assert ops.GetForm(affix) == f"{TEST_PREFIX}suf"
            assert ops.GetForm(affix.Hvo) == f"{TEST_PREFIX}suf"
            assert ops.GetForm(stem) == f"{TEST_PREFIX}stem"
            assert ops.GetForm(stem.Hvo) == f"{TEST_PREFIX}stem"
            wrappers = {
                w.Hvo: w for w in ops.GetAll(entry)
            }
            assert affix.Hvo in wrappers
            assert ops.GetForm(wrappers[affix.Hvo]) == f"{TEST_PREFIX}suf"
        finally:
            sandbox.LexEntry.Delete(entry)
