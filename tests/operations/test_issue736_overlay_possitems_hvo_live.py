#
#   test_issue736_overlay_possitems_hvo_live.py
#
#   Live verification for issue #736 Overlay PossItemsRC HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_736_"


@pytest.mark.requires_live_project
class TestIssue736OverlayPossItemsRcHvoLive:
    """AddElement/RemoveElement must not rely on Python proxy identity in PossItemsRC."""

    @pytest.mark.live_phase("OverlayOperations", "modify")
    def test_remove_element_via_bare_object_view(self, sena3_sandbox):
        import SIL.LCModel as LCM

        project = sena3_sandbox
        lp = project.lp
        overlay_ops = project.Overlays

        conf_items = list(lp.ConfidenceLevelsOA.PossibilitiesOS)
        assert conf_items, "Sena 3 ConfidenceLevelsOA must have at least one item"
        seed_item = conf_items[0]

        factory = project.project.ServiceLocator.GetService(LCM.ICmOverlayFactory)
        overlay = None
        try:
            with overlay_ops._TransactionCM("test: create overlay for #736 remove"):
                overlay = factory.Create()
                lp.OverlaysOC.Add(overlay)
                overlay_ops.AddElement(overlay, seed_item)

            assert len(overlay_ops.GetPossItems(overlay)) == 1

            bare_item = project.Object(seed_item.Hvo)
            overlay_ops.RemoveElement(overlay, bare_item)
            assert len(overlay_ops.GetPossItems(overlay)) == 0
        finally:
            if overlay is not None:
                with overlay_ops._TransactionCM("test: cleanup overlay #736 remove"):
                    if overlay in lp.OverlaysOC:
                        lp.OverlaysOC.Remove(overlay)

    @pytest.mark.live_phase("OverlayOperations", "modify")
    def test_add_element_skips_duplicate_for_bare_object_view(self, sena3_sandbox):
        import SIL.LCModel as LCM

        project = sena3_sandbox
        lp = project.lp
        overlay_ops = project.Overlays

        conf_items = list(lp.ConfidenceLevelsOA.PossibilitiesOS)
        assert conf_items, "Sena 3 ConfidenceLevelsOA must have at least one item"
        seed_item = conf_items[0]

        factory = project.project.ServiceLocator.GetService(LCM.ICmOverlayFactory)
        overlay = None
        try:
            with overlay_ops._TransactionCM("test: create overlay for #736 add dup"):
                overlay = factory.Create()
                lp.OverlaysOC.Add(overlay)
                overlay_ops.AddElement(overlay, seed_item)

            assert len(overlay_ops.GetPossItems(overlay)) == 1

            bare_item = project.Object(seed_item.Hvo)
            overlay_ops.AddElement(overlay, bare_item)
            assert len(overlay_ops.GetPossItems(overlay)) == 1
        finally:
            if overlay is not None:
                with overlay_ops._TransactionCM("test: cleanup overlay #736 add dup"):
                    if overlay in lp.OverlaysOC:
                        lp.OverlaysOC.Remove(overlay)
