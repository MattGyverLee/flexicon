#
#   test_547_addsubcat_catalog_live.py
#
#   Live verification for issue #547: POSOperations.AddSubcategory
#   accepts catalogSourceId like Create, and Create is canonical with
#   parent=None while AddSubcategory delegates to it.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_547_"
ADJECTIVE_CANONICAL_GUID = "30d07580-5052-4d91-bc24-469b8b2d7df9"


def _find_pos_by_guid(project, guid_str):
    target = guid_str.lower()
    for pos in project.POS.GetAll(recursive=True):
        try:
            if str(pos.Guid).lower() == target:
                return pos
        except Exception:
            continue
    return None


class TestAddSubcategoryCatalogSourceId:
    @pytest.mark.live_phase("POSOperations", "add")
    def test_verbatim_id_sets_catalog_and_parent(self, target_sandbox):
        parent = target_sandbox.POS.Create(
            f"{TEST_PREFIX}Parent", f"{TEST_PREFIX}P"
        )
        try:
            sub = target_sandbox.POS.AddSubcategory(
                parent,
                f"{TEST_PREFIX}Sub",
                f"{TEST_PREFIX}S",
                catalogSourceId="ProjectSpecific:547Foo",
            )
            assert sub is not None
            # Read back from the LCM, not the passed-in value alone.
            assert target_sandbox.POS.GetCatalogSourceId(sub) == "ProjectSpecific:547Foo"
            assert sub.CatalogSourceId == "ProjectSpecific:547Foo"
            got_parent = target_sandbox.POS.GetParent(sub)
            assert got_parent is not None
            assert str(got_parent.Guid) == str(parent.Guid)
        finally:
            # RemoveSubcategory removes from parent; parent deleted after.
            try:
                target_sandbox.POS.RemoveSubcategory(parent, sub)
            except Exception:
                pass
            target_sandbox.POS.Delete(parent)

    @pytest.mark.live_phase("POSOperations", "add")
    def test_default_none_preserves_old_behavior(self, target_sandbox):
        parent = target_sandbox.POS.Create(
            f"{TEST_PREFIX}Parent2", f"{TEST_PREFIX}P2"
        )
        try:
            sub = target_sandbox.POS.AddSubcategory(
                parent, f"{TEST_PREFIX}Sub2", f"{TEST_PREFIX}S2"
            )
            assert sub is not None
            assert target_sandbox.POS.GetCatalogSourceId(sub) == ""
        finally:
            try:
                target_sandbox.POS.RemoveSubcategory(parent, sub)
            except Exception:
                pass
            target_sandbox.POS.Delete(parent)

    @pytest.mark.live_phase("POSOperations", "add")
    def test_gold_id_takes_catalog_path(self, target_sandbox):
        pre_existing = _find_pos_by_guid(target_sandbox, ADJECTIVE_CANONICAL_GUID)
        parent = target_sandbox.POS.Create(
            f"{TEST_PREFIX}ParentGold", f"{TEST_PREFIX}PG"
        )
        created_guid = None
        try:
            sub = target_sandbox.POS.AddSubcategory(
                parent,
                f"{TEST_PREFIX}GoldSub",
                f"{TEST_PREFIX}GS",
                catalogSourceId="GOLD:Adjective",
            )
            assert sub is not None
            actual_guid = str(sub.Guid).lower()
            assert actual_guid == ADJECTIVE_CANONICAL_GUID
            if pre_existing is None:
                created_guid = ADJECTIVE_CANONICAL_GUID
                # Newly created: must be parented under our parent.
                got_parent = target_sandbox.POS.GetParent(sub)
                assert got_parent is not None
                assert str(got_parent.Guid) == str(parent.Guid)
            # Name overlay in default analysis WS.
            anal_ws = target_sandbox.project.DefaultAnalWs
            assert target_sandbox.POS.GetName(sub, anal_ws) == f"{TEST_PREFIX}GoldSub"
            assert target_sandbox.POS.GetAbbreviation(sub, anal_ws) == f"{TEST_PREFIX}GS"
        finally:
            if created_guid is not None:
                # New catalog item: detach from parent then delete by GUID.
                try:
                    obj = _find_pos_by_guid(target_sandbox, created_guid)
                    if obj is not None:
                        par = target_sandbox.POS.GetParent(obj)
                        if par is not None:
                            target_sandbox.POS.RemoveSubcategory(par, obj)
                        else:
                            target_sandbox.POS.Delete(obj)
                except Exception:
                    pass
            try:
                target_sandbox.POS.Delete(parent)
            except Exception:
                pass


class TestCreateParentDelegation:
    @pytest.mark.live_phase("POSOperations", "add")
    def test_create_with_parent_matches_addsubcategory(self, target_sandbox):
        """Create(parent=...) and AddSubcategory produce the same shape."""
        parent = target_sandbox.POS.Create(
            f"{TEST_PREFIX}CanonParent", f"{TEST_PREFIX}CP"
        )
        try:
            via_create = target_sandbox.POS.Create(
                f"{TEST_PREFIX}ViaCreate",
                f"{TEST_PREFIX}VC",
                catalogSourceId="ProjectSpecific:547Bar",
                parent=parent,
            )
            via_addsub = target_sandbox.POS.AddSubcategory(
                parent,
                f"{TEST_PREFIX}ViaAddSub",
                f"{TEST_PREFIX}VA",
                catalogSourceId="ProjectSpecific:547Bar",
            )
            for sub in (via_create, via_addsub):
                assert sub is not None
                assert target_sandbox.POS.GetCatalogSourceId(sub) == "ProjectSpecific:547Bar"
                got_parent = target_sandbox.POS.GetParent(sub)
                assert got_parent is not None
                assert str(got_parent.Guid) == str(parent.Guid)
        finally:
            for sub in list(target_sandbox.POS.GetSubcategories(parent, recursive=False)):
                try:
                    target_sandbox.POS.RemoveSubcategory(parent, sub)
                except Exception:
                    pass
            target_sandbox.POS.Delete(parent)

    @pytest.mark.live_phase("POSOperations", "add")
    def test_create_with_hvo_parent(self, target_sandbox):
        """Create accepts an HVO parent, like AddSubcategory does."""
        parent = target_sandbox.POS.Create(
            f"{TEST_PREFIX}HvoParent", f"{TEST_PREFIX}HP"
        )
        try:
            sub = target_sandbox.POS.Create(
                f"{TEST_PREFIX}HvoSub", f"{TEST_PREFIX}HS", parent=parent.Hvo
            )
            assert sub is not None
            got_parent = target_sandbox.POS.GetParent(sub)
            assert got_parent is not None
            assert str(got_parent.Guid) == str(parent.Guid)
        finally:
            for sub in list(target_sandbox.POS.GetSubcategories(parent, recursive=False)):
                try:
                    target_sandbox.POS.RemoveSubcategory(parent, sub)
                except Exception:
                    pass
            target_sandbox.POS.Delete(parent)
