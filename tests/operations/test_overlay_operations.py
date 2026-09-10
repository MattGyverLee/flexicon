#
#   test_overlay_operations.py
#
#   Class: OverlayOperations
#          Regression coverage for issue #277 (OverlayOperations half):
#          GetPossItems() read `overlay.SubPossibilitiesOS`, a property
#          that does not exist on ICmOverlay (whose complete own-declared
#          surface is Name, PossItemsRC, PossListRA -- confirmed by live
#          reflection, see specs/277-nonexistent-property-reads/evidence/
#          live-277-overlays.md). The `hasattr` guard was always False,
#          so the method returned [] unconditionally, for every overlay,
#          regardless of its actual contents.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import inspect

import pytest


# ---------------------------------------------------------------------------
# Offline test: pins the source-level property-name claim so a future
# regression (reintroducing SubPossibilitiesOS, or dropping PossItemsRC)
# fails fast without needing a live FieldWorks install. This is the
# "static" half of the regression coverage requested when live
# verification is unavailable; here it is additive to the live tests
# below, not a substitute for them (a live overlay was available).
# ---------------------------------------------------------------------------


def test_get_poss_items_reads_possitemsrc_not_subpossibilitiesos():
    """
    Source-level ratchet: GetPossItems must read ICmOverlay.PossItemsRC.

    ICmOverlay has no SubPossibilitiesOS (that is a ICmPossibility-only
    property; ICmOverlay is not a ICmPossibility -- confirmed live,
    ICmPossibility.IsAssignableFrom(ICmOverlay) is False). Guards against
    silently reverting to the always-empty-list defect.
    """
    from flexicon.code.Lists.OverlayOperations import OverlayOperations
    from flexicon.code.BaseOperations import OperationsMethod

    # GetPossItems is wrapped in the OperationsMethod descriptor (see
    # BaseOperations.py), which returns a `class_method` closure from
    # __get__ rather than the original function -- accessing it through
    # the class (OverlayOperations.GetPossItems) would inspect that
    # closure instead of the real method body. Pull the raw function
    # straight out of the descriptor via __dict__ to bypass __get__.
    descriptor = OverlayOperations.__dict__["GetPossItems"]
    assert isinstance(descriptor, OperationsMethod), (
        "GetPossItems is no longer wrapped in OperationsMethod -- update "
        "this test's unwrapping to match the new decoration."
    )
    source = inspect.getsource(descriptor.func)

    assert "PossItemsRC" in source, (
        "GetPossItems() no longer reads PossItemsRC -- this is the only "
        "real possibility-item property on ICmOverlay (issue #277)."
    )
    assert 'hasattr(overlay, "SubPossibilitiesOS")' not in source, (
        "GetPossItems() guards on SubPossibilitiesOS again -- that "
        "property does not exist on ICmOverlay so the hasattr guard is "
        "always False, silently regressing to returning [] always "
        "(issue #277)."
    )


# ---------------------------------------------------------------------------
# Live tests
# ---------------------------------------------------------------------------


class TestGetPossItemsLive:
    """
    Live-DB coverage against a Sena 3 sandbox (fresh temp copy per test,
    per tests/flex_plugin.py's sena3_sandbox fixture -- never touches the
    user's real Sena 3).

    OverlayOperations.Create()/GetAll() are inherited from
    PossibilityItemOperations and are broken for a different reason
    (_get_list_object() returns None by design, since ICmOverlay is not
    backed by a ICmPossibilityList) -- see the finding recorded in the
    evidence file. These tests therefore construct/locate ICmOverlay
    objects directly via the LCM (project.lp.OverlaysOC /
    ICmOverlayFactory), exactly as a real caller would have to today,
    and exercise only GetPossItems() through the Operations class.
    """

    pytestmark = pytest.mark.requires_live_project

    @pytest.mark.live_phase("OverlayOperations", "read")
    def test_returns_real_items_for_preexisting_overlay(self, sena3_sandbox):
        """
        Sena 3 ships with one pre-existing overlay carrying live
        PossItemsRC content. Before the fix this returned [] for every
        overlay; after the fix it must return exactly what PossItemsRC
        holds. Read-only -- does not mutate the pre-existing overlay.
        """
        project = sena3_sandbox
        lp = project.lp

        existing = list(lp.OverlaysOC)
        if not existing:
            pytest.skip(
                "No pre-existing overlay in the Sena 3 fixture; see "
                "test_returns_seeded_items_for_freshly_created_overlay "
                "for the create-and-verify path instead."
            )

        overlay = existing[0]
        expected = list(overlay.PossItemsRC)

        result = project.Overlays.GetPossItems(overlay)

        assert len(expected) > 0, (
            "Precondition failed: the pre-existing overlay's PossItemsRC "
            "is empty, so this test cannot distinguish 'fixed' from "
            "'still always returns []'."
        )
        assert len(result) == len(expected), (
            f"GetPossItems() returned {len(result)} items, expected "
            f"{len(expected)} (matching overlay.PossItemsRC directly)."
        )
        result_hvos = {o.Hvo for o in result}
        expected_hvos = {o.Hvo for o in expected}
        assert result_hvos == expected_hvos

    @pytest.mark.live_phase("OverlayOperations", "add")
    def test_returns_seeded_items_for_freshly_created_overlay(self, sena3_sandbox):
        """
        Create a throwaway ICmOverlay directly via the LCM (bypassing
        the separately-broken Create()/_get_list_object() path), seed
        it with 2 real possibility items borrowed from
        ConfidenceLevelsOA, and confirm GetPossItems() surfaces exactly
        those items. Cleans up in `finally`.
        """
        import SIL.LCModel as LCM

        project = sena3_sandbox
        lp = project.lp
        overlay_ops = project.Overlays

        conf_items = list(lp.ConfidenceLevelsOA.PossibilitiesOS)
        assert len(conf_items) >= 2, (
            "Precondition failed: Sena 3 fixture's ConfidenceLevelsOA "
            "has fewer than 2 items to seed the test overlay with."
        )
        seed_items = conf_items[:2]

        factory = project.project.ServiceLocator.GetService(LCM.ICmOverlayFactory)
        overlay = None
        try:
            with overlay_ops._TransactionCM("test: create seeded overlay"):
                overlay = factory.Create()
                lp.OverlaysOC.Add(overlay)
                for item in seed_items:
                    overlay.PossItemsRC.Add(item)

            result = overlay_ops.GetPossItems(overlay)

            assert len(result) == 2, (
                f"Expected 2 seeded items, GetPossItems() returned "
                f"{len(result)}."
            )
            result_hvos = {o.Hvo for o in result}
            seed_hvos = {o.Hvo for o in seed_items}
            assert result_hvos == seed_hvos
        finally:
            if overlay is not None:
                with overlay_ops._TransactionCM("test: cleanup seeded overlay"):
                    if overlay in lp.OverlaysOC:
                        lp.OverlaysOC.Remove(overlay)

    @pytest.mark.live_phase("OverlayOperations", "add")
    def test_returns_empty_list_for_overlay_with_no_items(self, sena3_sandbox):
        """
        An overlay with a genuinely empty PossItemsRC must still return
        [] -- distinguishing the correct "no items" case from the
        pre-fix "always []" defect (covered by the two tests above).
        """
        import SIL.LCModel as LCM

        project = sena3_sandbox
        lp = project.lp
        overlay_ops = project.Overlays

        factory = project.project.ServiceLocator.GetService(LCM.ICmOverlayFactory)
        overlay = None
        try:
            with overlay_ops._TransactionCM("test: create empty overlay"):
                overlay = factory.Create()
                lp.OverlaysOC.Add(overlay)

            result = overlay_ops.GetPossItems(overlay)
            assert result == []
        finally:
            if overlay is not None:
                with overlay_ops._TransactionCM("test: cleanup empty overlay"):
                    if overlay in lp.OverlaysOC:
                        lp.OverlaysOC.Remove(overlay)
