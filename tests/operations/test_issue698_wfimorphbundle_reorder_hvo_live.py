#
#   test_issue698_wfimorphbundle_reorder_hvo_live.py
#
#   Live verification for issue #698 WfiMorphBundle Reorder HVO membership partition.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_698_"


class TestIssue698WfiMorphBundleReorderHvoLive:
    """Reorder must accept Object(hvo) views in bundle_list."""

    @pytest.mark.live_phase("WfiMorphBundleOperations", "write")
    def test_reorder_with_raw_object_views(self, target_sandbox):
        wordforms = target_sandbox.Wordforms
        analyses = target_sandbox.WfiAnalyses
        bundles = target_sandbox.WfiMorphBundles

        wf = wordforms.Create(f"{TEST_PREFIX}wf")
        analysis = analyses.Create(wf)
        b0 = bundles.Create(analysis)
        b1 = bundles.Create(analysis)

        try:
            raw_first = target_sandbox.Object(b0.Hvo)
            raw_second = target_sandbox.Object(b1.Hvo)
            bundles.Reorder(analysis, [raw_second, raw_first])

            order = [b.Hvo for b in analysis.MorphBundlesOS]
            assert order == [b1.Hvo, b0.Hvo]
        finally:
            bundles.Delete(b1)
            bundles.Delete(b0)
            analyses.Delete(analysis)
            wordforms.Delete(wf)
