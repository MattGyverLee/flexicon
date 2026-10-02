#
#   test_issue603_semdom_getall.py
#
#   SemanticDomainOperations.GetAll(recursive=False) must return only
#   top-level ICmSemanticDomain objects, never nested Python lists
#   (issue #603). Same shape fixed in AnthropologyOperations and
#   LocationOperations.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

from unittest.mock import MagicMock, patch

import pytest

from flexicon.code.Lexicon import SemanticDomainOperations as sdo_mod
from flexicon.code.Notebook import AnthropologyOperations as anth_mod
from flexicon.code.Notebook import LocationOperations as loc_mod


def _bare(ops_cls, project):
    ops = ops_cls.__new__(ops_cls)
    ops.project = project
    return ops


def _unpack_like_flexproject(items, cls, flat=False):
    """Same contract as FLExProject.UnpackNestedPossibilityList."""
    for i in items:
        yield cls(i)
        sub = getattr(i, "Subs", [])
        if flat:
            for j in _unpack_like_flexproject(sub, cls, flat):
                yield cls(j)
        else:
            nested = list(_unpack_like_flexproject(sub, cls, flat))
            if nested:
                yield nested


class _Item:
    def __init__(self, name, subs=()):
        self.name = name
        self.Subs = list(subs)


def _tree():
    return [_Item("a", [_Item("a1", [_Item("a1x")]), _Item("a2")]), _Item("b")]


class _Cast:
    """Stand-in for an LCM interface cast: wraps and exposes the item."""
    def __init__(self, item):
        self.item = item


CASES = [
    (sdo_mod, "SemanticDomainOperations", "ICmSemanticDomain", "SemanticDomainListOA"),
    (anth_mod, "AnthropologyOperations", "ICmAnthroItem", "AnthroListOA"),
    (loc_mod, "LocationOperations", "ICmLocation", "LocationsOA"),
]


@pytest.mark.parametrize("mod,cls_name,iface,list_attr", CASES)
class TestGetAllRecursiveFalse:
    def _ops(self, mod, cls_name, iface, list_attr):
        project = MagicMock()
        plist = MagicMock()
        plist.PossibilitiesOS = _tree()
        setattr(project.lp, list_attr, plist)
        project.UnpackNestedPossibilityList = _unpack_like_flexproject
        ops = _bare(getattr(mod, cls_name), project)
        return ops

    def test_non_recursive_returns_only_top_level_items(self, mod, cls_name, iface, list_attr):
        ops = self._ops(mod, cls_name, iface, list_attr)
        with patch.object(mod, iface, _Cast):
            result = ops.GetAll(recursive=False)
        assert len(result) == 2
        assert all(isinstance(r, _Cast) for r in result)
        assert [r.item.name for r in result] == ["a", "b"]

    def test_recursive_returns_flat_items_only(self, mod, cls_name, iface, list_attr):
        ops = self._ops(mod, cls_name, iface, list_attr)
        with patch.object(mod, iface, _Cast):
            result = ops.GetAll(recursive=True)
        assert not any(isinstance(r, list) for r in result)
        assert len(result) == 5


@pytest.mark.requires_live_project
class TestSemanticDomainGetAllLive:
    """Read-only checks against a fresh sandbox copy of Sena 3."""

    @pytest.mark.live_phase("SemanticDomainOperations", "read")
    def test_getall_non_recursive_matches_top_level_count(self, sena3_sandbox):
        from SIL.LCModel import ICmSemanticDomain

        sd = sena3_sandbox.SemanticDomains
        top_count = sena3_sandbox.lp.SemanticDomainListOA.PossibilitiesOS.Count
        assert top_count > 0, "Sena 3 sandbox has no semantic domains"

        top = sd.GetAll(recursive=False)
        print(f"[INFO] top_count={top_count} GetAll(False)={len(top)}")
        assert len(top) == top_count
        assert all(not isinstance(d, list) for d in top)
        assert all(isinstance(d, ICmSemanticDomain) for d in top)
        # docstring example must work
        for d in top:
            sd.GetName(d)

    @pytest.mark.live_phase("SemanticDomainOperations", "read")
    def test_getall_recursive_is_flat_domains_superset(self, sena3_sandbox):
        from SIL.LCModel import ICmSemanticDomain

        sd = sena3_sandbox.SemanticDomains
        top = sd.GetAll(recursive=False)
        everything = sd.GetAll(recursive=True)
        assert all(isinstance(d, ICmSemanticDomain) for d in everything)
        print(f"[INFO] recursive={len(everything)} top={len(top)}")
        assert len(everything) > len(top)
        expected = len(top) + sum(len(sd.GetSubdomains(d)) for d in top)
        assert len(everything) == expected
