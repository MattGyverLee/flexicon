#
#   test_issue533_wfimorphbundle_duplicate_hvo_live.py
#
#   Live verification for issue #533 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_533_"


class TestIssue533WfiMorphBundleDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("WfiMorphBundleOperations", "write")
    def test_duplicate_insert_after_raw_object_view(self, target_sandbox):
        wordforms = target_sandbox.Wordforms
        analyses = target_sandbox.WfiAnalyses
        bundles = target_sandbox.WfiMorphBundles

        wf = wordforms.Create(f"{TEST_PREFIX}wf")
        analysis = analyses.Create(wf)
        b0 = bundles.Create(analysis)
        b1 = bundles.Create(analysis)
        b2 = bundles.Create(analysis)

        raw_mid = target_sandbox.Object(b1.Hvo)
        dup = bundles.Duplicate(raw_mid, insert_after=True, deep=False)

        order = [b.Hvo for b in analysis.MorphBundlesOS]
        assert order.index(dup.Hvo) == order.index(b1.Hvo) + 1

        bundles.Delete(dup)
        bundles.Delete(b2)
        bundles.Delete(b1)
        bundles.Delete(b0)
        analyses.Delete(analysis)
        wordforms.Delete(wf)
