#
#   test_issue786_wfimorphbundle_delete_hvo_live.py
#
#   Live verification for issue #786 WfiMorphBundleOperations Delete HVO lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_786_"


def test_issue786_delete_removes_from_morphbundlesos_by_hvo(target_sandbox):
    """Delete removes a morph bundle when the caller passes a bare Object(hvo) view."""
    project = target_sandbox
    wf = project.Wordforms.Create(f"{TEST_PREFIX}wf")
    try:
        analysis = project.WfiAnalyses.Create(wf)
        bundle = project.WfiMorphBundles.Create(analysis)
        assert analysis.MorphBundlesOS.Count >= 1
        hvo = bundle.Hvo
        bare_view = project.Object(hvo)
        starting = analysis.MorphBundlesOS.Count
        project.WfiMorphBundles.Delete(bare_view)
        assert analysis.MorphBundlesOS.Count == starting - 1
        remaining = {int(b.Hvo) for b in analysis.MorphBundlesOS}
        assert int(hvo) not in remaining
    finally:
        project.Wordforms.Delete(wf)
