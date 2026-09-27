#
#   test_569_create_parent_sweep_live.py
#
#   Live verification for issue #569: Create is canonical with
#   parent=None in Anthropology, Location and DataNotebook;
#   CreateSubitem / CreateSublocation / CreateSubRecord delegate.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_569_"


class TestAnthropologyCreateParent:
    @pytest.mark.live_phase("AnthropologyOperations", "add")
    def test_create_with_parent_matches_createsubitem(self, target_sandbox):
        ops = target_sandbox.Anthropology
        parent = ops.Create(f"{TEST_PREFIX}Parent")
        try:
            via_create = ops.Create(
                f"{TEST_PREFIX}ViaCreate", "VC", "586.1", parent=parent
            )
            via_sub = ops.CreateSubitem(parent, f"{TEST_PREFIX}ViaSub", "VS", "586.2")
            for sub in (via_create, via_sub):
                assert ops.GetParent(sub).Hvo == parent.Hvo
            subs = list(ops.GetSubitems(parent))
            assert {s.Hvo for s in subs} >= {via_create.Hvo, via_sub.Hvo}
            # OCM-code handling is shared code: both paths must agree
            # (live LCM exposes no AnthroCode member, so both read back
            # empty -- the point is parity, not the value).
            assert ops.GetAnthroCode(via_create) == ops.GetAnthroCode(via_sub)
        finally:
            ops.Delete(parent)

    @pytest.mark.live_phase("AnthropologyOperations", "add")
    def test_sub_path_keeps_frozen_whitespace_semantics(self, target_sandbox):
        # PN13: padded subitem name persists verbatim, no dedup -- a
        # duplicate subitem name must SUCCEED (spec.md C5).
        ops = target_sandbox.Anthropology
        parent = ops.Create(f"{TEST_PREFIX}WsParent")
        try:
            padded = f"{TEST_PREFIX}Padded "
            first = ops.Create(padded, parent=parent)
            second = ops.CreateSubitem(parent, padded)
            ws = target_sandbox.project.DefaultAnalWs
            from SIL.LCModel.Core.KernelInterfaces import ITsString

            assert ITsString(first.Name.get_String(ws)).Text == padded
            assert ITsString(second.Name.get_String(ws)).Text == padded
            # PN14: non-str raises AttributeError on the canonical path.
            with pytest.raises(AttributeError):
                ops.Create(object(), parent=parent)
        finally:
            ops.Delete(parent)


class TestLocationCreateParent:
    @pytest.mark.live_phase("LocationOperations", "add")
    def test_create_with_parent_matches_createsublocation(self, target_sandbox):
        ops = target_sandbox.Location
        country = ops.Create(f"{TEST_PREFIX}Country")
        try:
            via_create = ops.Create(
                f"{TEST_PREFIX}ViaCreate", alias="T569VC", parent=country
            )
            via_sub = ops.CreateSublocation(
                country, f"{TEST_PREFIX}ViaSub", alias="T569VS"
            )
            for sub in (via_create, via_sub):
                assert ops.GetRegion(sub).Hvo == country.Hvo
            subs = list(ops.GetSublocations(country))
            assert {s.Hvo for s in subs} >= {via_create.Hvo, via_sub.Hvo}
            assert ops.GetAlias(via_create) == "T569VC"
        finally:
            ops.Delete(country)

    @pytest.mark.live_phase("LocationOperations", "add")
    def test_create_with_hvo_parent(self, target_sandbox):
        ops = target_sandbox.Location
        country = ops.Create(f"{TEST_PREFIX}HvoCountry")
        try:
            town = ops.Create(f"{TEST_PREFIX}HvoTown", parent=country.Hvo)
            assert ops.GetRegion(town).Hvo == country.Hvo
        finally:
            ops.Delete(country)


class TestDataNotebookCreateParent:
    @pytest.mark.live_phase("DataNotebookOperations", "add")
    def test_create_with_parent_matches_createsubrecord(self, target_sandbox):
        ops = target_sandbox.DataNotebook
        parent = ops.Create(f"{TEST_PREFIX}Parent")
        try:
            via_create = ops.Create(
                f"{TEST_PREFIX}ViaCreate",
                content=f"{TEST_PREFIX}content",
                parent=parent,
            )
            via_sub = ops.CreateSubRecord(
                parent, f"{TEST_PREFIX}ViaSub", content=f"{TEST_PREFIX}content2"
            )
            for sub in (via_create, via_sub):
                assert ops.GetParentRecord(sub).Hvo == parent.Hvo
            subs = list(ops.GetSubRecords(parent))
            assert {s.Hvo for s in subs} >= {via_create.Hvo, via_sub.Hvo}
            assert ops.GetParentRecord(parent) is None
        finally:
            ops.Delete(parent)
