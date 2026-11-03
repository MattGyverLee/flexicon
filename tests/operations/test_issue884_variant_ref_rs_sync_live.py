#
#   test_issue884_variant_ref_rs_sync_live.py
#
#   Issue #884: ILexEntryRef RS fields in VariantOperations sync surface.
#   Verified on target_sandbox (tempdir copy only).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest


def _first_variant_ref(project):
    for entry in project.LexEntry.GetAll():
        refs = list(project.Variants.GetAll(entry))
        if refs:
            return refs[0]
    return None


@pytest.mark.requires_live_project
class TestIssue884VariantRefRsSyncLive:

    def test_variant_entry_types_rs_roundtrip(self, target_sandbox):
        p = target_sandbox
        ref = _first_variant_ref(p)
        if ref is None:
            pytest.skip("no ILexEntryRef rows in sandbox project")

        props = p.Variants.GetSyncableProperties(ref)
        assert "variant_entry_types_rs" in props
        source_guids = list(props["variant_entry_types_rs"])
        if not source_guids:
            pytest.skip("variant ref has empty VariantEntryTypesRS")

        p.Variants.ApplySyncableProperties(ref, props)
        after = p.Variants.GetSyncableProperties(ref)
        assert after["variant_entry_types_rs"] == source_guids
