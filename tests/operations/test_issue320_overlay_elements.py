#
#   test_issue320_overlay_elements.py
#
#   Class: OverlayOperations
#          Regression coverage for issue #320:
#          GetElements()/AddElement()/RemoveElement() branched on
#          `overlay.InstancesOS` and `overlay.Elements`. Neither property
#          exists anywhere on `ICmOverlay` in LCM 11 (whole-index grep for
#          both names returns zero hits) -- `ICmOverlay`'s complete
#          own-declared property surface is `Name`, `PossItemsRC`,
#          `PossListRA`. Both `hasattr` branches were always `False`, so
#          all three methods were unconditional no-ops: GetElements()
#          always returned [], AddElement()/RemoveElement() silently did
#          nothing.
#
#          Fix: rewrite against `PossItemsRC` (a reference collection --
#          add/remove only link/unlink, never affecting the underlying
#          ICmPossibility's lifetime), mirroring the already-correct
#          GetPossItems() in the same file. The dead hasattr branches are
#          deleted, not kept as fallbacks. AddElement() additionally
#          checks that the element is a member of the possibility list
#          the overlay is bound to (overlay.PossListRA); cycle-2 live
#          evidence (specs/318-321-nonexistent-member-mutations/evidence/
#          live-cycle2-business-rules.md) showed the LCM layer is
#          permissive about this (a foreign possibility was added without
#          exception and persisted), so as of cycle 3 the guard warns and
#          proceeds rather than raising -- see the team-lead ruling and
#          the comment at the guard site in OverlayOperations.py.
#
#          Every assertion re-reads PossItemsRC membership fresh after
#          the mutating call, rather than trusting a stale handle or "no
#          exception raised" -- that shallower assertion passes against
#          the pre-fix broken code too, which is exactly why #320 shipped.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import inspect
import sys
import os

import pytest

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
sys.path.insert(0, _project_root)

from tests.operations import mock_flex_project, MockLCMObject


# ---------------------------------------------------------------------------
# Minimal mock objects -- no LCM / FieldWorks required
# ---------------------------------------------------------------------------


class _MockReferenceCollection:
    """Stand-in for ILcmReferenceCollection (PossItemsRC). Add/Remove never
    affect the referenced object's lifetime -- purely link/unlink."""

    def __init__(self, items=None):
        self._items = list(items) if items else []

    def __iter__(self):
        return iter(list(self._items))

    def __len__(self):
        return len(self._items)

    def __contains__(self, item):
        return item in self._items

    def Add(self, item):
        if item not in self._items:
            self._items.append(item)

    def Remove(self, item):
        self._items.remove(item)


class _MockPossibilityList(MockLCMObject):
    """Stand-in for ICmPossibilityList -- only .Hvo is compared."""


class _MockOverlay(MockLCMObject):
    """Stand-in for ICmOverlay: Name, PossItemsRC, PossListRA."""

    def __init__(self, hvo, poss_items=None, poss_list=None):
        super().__init__(hvo=hvo)
        self.PossItemsRC = _MockReferenceCollection(poss_items)
        self.PossListRA = poss_list


def _make_possibility(hvo, owning_list=None):
    """A mock ICmPossibility, optionally tagged with its owning list."""
    item = MockLCMObject(hvo=hvo)
    item.OwningList = owning_list
    return item


def _make_ops(mock_flex_project):
    from flexicon.code.Lists.OverlayOperations import OverlayOperations

    mock_flex_project.writeEnabled = True
    return OverlayOperations(mock_flex_project)


# ===========================================================================
# GetElements
# ===========================================================================


class TestGetElements:
    def test_returns_actual_possitemsrc_members(self, mock_flex_project):
        ops = _make_ops(mock_flex_project)
        item1 = _make_possibility(hvo=10)
        item2 = _make_possibility(hvo=11)
        overlay = _MockOverlay(hvo=1, poss_items=[item1, item2])

        result = ops.GetElements(overlay)

        assert len(result) == 2, (
            "GetElements() did not return the overlay's real PossItemsRC "
            "content -- the pre-fix code always returned [] regardless "
            "of contents (issue #320)."
        )
        result_hvos = {o.Hvo for o in result}
        assert result_hvos == {10, 11}

    def test_empty_overlay_returns_empty_list(self, mock_flex_project):
        ops = _make_ops(mock_flex_project)
        overlay = _MockOverlay(hvo=1, poss_items=[])

        assert ops.GetElements(overlay) == []


# ===========================================================================
# AddElement
# ===========================================================================


class TestAddElement:
    def test_add_element_actually_mutates_possitemsrc(self, mock_flex_project):
        """Pre-fix: AddElement() checked overlay.InstancesOS/overlay.Elements
        (neither exists), so this was a silent no-op regardless of the
        return value. Post-fix: PossItemsRC membership changes, re-read
        fresh from the overlay afterward."""
        ops = _make_ops(mock_flex_project)
        poss_list = _MockPossibilityList(hvo=50)
        overlay = _MockOverlay(hvo=1, poss_items=[], poss_list=poss_list)
        item = _make_possibility(hvo=10, owning_list=poss_list)

        assert item not in overlay.PossItemsRC

        ops.AddElement(overlay, item)

        assert item in overlay.PossItemsRC, (
            "AddElement() did not add the element to PossItemsRC -- the "
            "exact silent-no-op shape of issue #320."
        )

    def test_add_element_is_idempotent(self, mock_flex_project):
        ops = _make_ops(mock_flex_project)
        poss_list = _MockPossibilityList(hvo=50)
        item = _make_possibility(hvo=10, owning_list=poss_list)
        overlay = _MockOverlay(hvo=1, poss_items=[item], poss_list=poss_list)

        ops.AddElement(overlay, item)

        assert len(list(overlay.PossItemsRC)) == 1

    def test_add_element_no_list_bound_skips_guard(self, mock_flex_project):
        """An overlay with no PossListRA set has nothing to validate
        membership against -- the guard must not block this case."""
        ops = _make_ops(mock_flex_project)
        overlay = _MockOverlay(hvo=1, poss_items=[], poss_list=None)
        item = _make_possibility(hvo=10, owning_list=None)

        ops.AddElement(overlay, item)

        assert item in overlay.PossItemsRC

    def test_add_element_not_member_of_bound_list_warns_and_proceeds(
        self, mock_flex_project, caplog
    ):
        """
        Team-lead ruling (#320, cycle 3): AddElement() must NOT reject a
        possibility that does not belong to the list the overlay is bound
        to (overlay.PossListRA). Cycle-2 live evidence
        (specs/318-321-nonexistent-member-mutations/evidence/
        live-cycle2-business-rules.md) showed the LCM layer is permissive
        here -- a foreign possibility was added without exception and
        persisted -- so the guard now warns and proceeds instead of
        raising.
        """
        ops = _make_ops(mock_flex_project)
        bound_list = _MockPossibilityList(hvo=50)
        other_list = _MockPossibilityList(hvo=99)
        overlay = _MockOverlay(hvo=1, poss_items=[], poss_list=bound_list)
        # Item belongs to a DIFFERENT list than the one the overlay is bound to.
        item = _make_possibility(hvo=10, owning_list=other_list)

        import logging

        with caplog.at_level(logging.WARNING, logger="flexicon.code.Lists.OverlayOperations"):
            ops.AddElement(overlay, item)

        # The add must genuinely succeed and persist ...
        assert item in overlay.PossItemsRC
        # ... but a warning must be logged flagging the non-membership.
        assert any(
            "not a member" in record.getMessage() for record in caplog.records
        )


# ===========================================================================
# RemoveElement
# ===========================================================================


class TestRemoveElement:
    def test_remove_element_actually_mutates_possitemsrc(self, mock_flex_project):
        ops = _make_ops(mock_flex_project)
        item1 = _make_possibility(hvo=10)
        item2 = _make_possibility(hvo=11)
        overlay = _MockOverlay(hvo=1, poss_items=[item1, item2])

        assert item1 in overlay.PossItemsRC

        ops.RemoveElement(overlay, item1)

        after = list(overlay.PossItemsRC)
        assert item1 not in after, (
            "RemoveElement() did not remove the element from PossItemsRC "
            "-- the exact silent-no-op shape of issue #320."
        )
        assert item2 in after

    def test_remove_absent_element_is_noop(self, mock_flex_project):
        ops = _make_ops(mock_flex_project)
        item1 = _make_possibility(hvo=10)
        absent = _make_possibility(hvo=999)
        overlay = _MockOverlay(hvo=1, poss_items=[item1])

        ops.RemoveElement(overlay, absent)

        assert list(overlay.PossItemsRC) == [item1]


# ===========================================================================
# Source-level ratchet: guards against reintroducing InstancesOS/Elements
# ===========================================================================


def _get_raw_func(descriptor_owner, method_name):
    """Unwrap the OperationsMethod descriptor to get the raw function body."""
    from flexicon.code.BaseOperations import OperationsMethod

    descriptor = descriptor_owner.__dict__[method_name]
    assert isinstance(descriptor, OperationsMethod), (
        f"{method_name} is no longer wrapped in OperationsMethod -- update "
        "this test's unwrapping to match the new decoration."
    )
    return inspect.getsource(descriptor.func)


@pytest.mark.parametrize("method_name", ["GetElements", "AddElement", "RemoveElement"])
def test_element_methods_do_not_read_nonexistent_properties(method_name):
    from flexicon.code.Lists.OverlayOperations import OverlayOperations

    source = _get_raw_func(OverlayOperations, method_name)

    assert 'hasattr(overlay, "InstancesOS")' not in source, (
        f"{method_name}() guards on InstancesOS again -- that property "
        "does not exist on ICmOverlay, so the hasattr guard is always "
        "False, silently regressing to a no-op (issue #320)."
    )
    assert 'hasattr(overlay, "Elements")' not in source, (
        f"{method_name}() guards on Elements again -- that property "
        "does not exist on ICmOverlay, so the hasattr guard is always "
        "False, silently regressing to a no-op (issue #320)."
    )
    assert "PossItemsRC" in source, (
        f"{method_name}() no longer reads PossItemsRC -- this is the "
        "only real element-holding property on ICmOverlay (issue #320)."
    )
