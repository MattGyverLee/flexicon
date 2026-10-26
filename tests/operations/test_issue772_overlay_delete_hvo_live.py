#
#   test_issue772_overlay_delete_hvo_live.py
#
#   Live verification for issue #772 OverlayOperations Delete HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project


def test_issue772_delete_removes_from_overlaysoc_by_hvo(sena3_sandbox):
    """Delete removes an overlay after re-fetching by HVO."""
    project = sena3_sandbox
    overlay_ops = project.Overlays
    poss_list = project.lp.ConfidenceLevelsOA
    test_name = "TEST_772_overlay_delete_hvo"

    existing = overlay_ops.Find(test_name)
    if existing is not None:
        overlay_ops.Delete(existing)

    overlay = overlay_ops.Create(test_name, poss_list)
    try:
        hvo = overlay.Hvo
        bare_view = project.Object(hvo)
        overlay_ops.Delete(bare_view)
        assert overlay_ops.Find(test_name) is None
        assert all(o.Hvo != hvo for o in overlay_ops.GetAll())
    finally:
        leftover = overlay_ops.Find(test_name)
        if leftover is not None:
            overlay_ops.Delete(leftover)
